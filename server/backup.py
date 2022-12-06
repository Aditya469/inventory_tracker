"""
Copyright 2022 DigitME2

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
from datetime import datetime
from shutil import copy

from filelock import Timeout
from flask import (
	Blueprint, request, make_response, jsonify
)

from auth import admin_access_required
from db import dbLock, close_db, getDbSession
from dbSchema import User, Settings
from emailNotification import sendEmail
from messages import getDatabaseBackupSuccessNotificationMessage, getDatabaseBackupFailureNotificationMessage
from paths import dbBackupDirPath, dbPath

bp = Blueprint('backup', __name__)


@bp.teardown_request
def afterRequest(self):
	close_db()


@bp.route("/initiateBackup", methods=("POST",))
@admin_access_required
def startBackupCommand():
	close_db() # necessary to allow DB lock to be obtained
	statusMessage, backupSucceeded = backUpDatabase()
	if backupSucceeded:
		return make_response(statusMessage, 200)
	else:
		return make_response(statusMessage, 500)


@bp.route("/getAvailableBackupNames")
@admin_access_required
def getAvailableBackupNames():
	backupNames = sorted(os.listdir(dbBackupDirPath))
	return make_response(jsonify(backupNames), 200)


@bp.route("/restoreDatabaseFromBackup", methods=("POST",))
@admin_access_required
def restoreDbFromBackup():
	close_db() # necessary to allow DB lock to be obtained
	error = None
	try:
		dbLock.acquire(timeout=10)
		if 'backupFileName' not in request.json:
			error = "No backup file name provided"
		else:
			backupFilePath = os.path.join(dbBackupDirPath, request.json.get("backupFileName"))
			if os.path.exists(dbPath):
				os.remove(dbPath)
			if not copy(backupFilePath, dbPath):
				error = "Failed to restore database"
	except Timeout:
		error = "Database is Locked"
	except IOError:
		error = "IO Error"
	finally:
		dbLock.release()

	if error:
		return make_response(error, 500)
	else:
		return make_response("Database Restored", 200)


def backUpDatabase():
	'''
	Moves each existing backup up one number, and then copies the existing database to the newly cleared position.
	'''
	backupFileNames = []
	dbSession = getDbSession()
	backupCount = dbSession.query(Settings.dbNumberOfBackups).first()[0]
	close_db()

	# get a list of backup file names. If we have reached the maximum count, delete the oldest. Ensure that the directory exists first
	if not os.path.exists(dbBackupDirPath):
		os.makedirs(dbBackupDirPath)

	backupNames = os.listdir(dbBackupDirPath)
	if len(backupNames) >= backupCount:
		oldestFileName = backupNames[0]
		oldestTimestamp = os.path.getctime(os.path.join(dbBackupDirPath, backupNames[0]))
		for backupName in backupNames:
			fileTimestamp = os.path.getctime(os.path.join(dbBackupDirPath, backupName))
			if fileTimestamp < oldestTimestamp:
				oldestFileName = backupName

		os.remove(os.path.join(dbBackupDirPath, oldestFileName))

	dbLock.acquire(timeout=10)
	try:
		now = datetime.now()
		newBackupFilename = f"db_backup_{now.year}-{now.month:0>2}-{now.day:0>2}_{now.hour:0>2}:{now.minute:0>2}:{now.second:0>2}.sqlite"
		backupFilePath = os.path.join(dbBackupDirPath, newBackupFilename)
		if copy(dbPath, backupFilePath):
			status = "Backup Complete"
			backupSucceeded = True
	except Timeout as e:
		status = "Backup Failed - Database is locked"
		backupSucceeded = False
		print(e)
	except IOError as e:
		status = "Backup Failed - IO Error"
		backupSucceeded = False
		print(e)
	finally:
		dbLock.release()

	# check if an email should be sent
	dbSession = getDbSession()
	settings = dbSession.query(Settings).first()
	if settings.sendEmails:
		emailAddressList = [row[0] for row in
							dbSession.query(User.emailAddress)
								.filter(User.receiveDbStatusNotifications == True)
								.all()
							]
		if backupSucceeded:
			message = getDatabaseBackupSuccessNotificationMessage(newBackupFilename)
			sendEmail(emailAddressList, "Inventory tracker database backup succeeded", message)
		else:
			message = getDatabaseBackupFailureNotificationMessage(status)
			sendEmail(emailAddressList, "ATTENTION REQUIRED. Inventory Tracker database backup failed", message)

	close_db()

	return status, backupSucceeded

