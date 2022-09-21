'''
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
'''

import os
import threading
import time

from flask import (
	Blueprint, render_template, request, make_response, jsonify, current_app
)
from werkzeug.utils import secure_filename

import db
from stockManagement import updateNewStockWithNewProduct
from auth import login_required, admin_access_required,create_access_required,edit_access_required
from dbSchema import ProductType, StockItem, User, Settings
from db import getDbSession, dbLock, dbPath, getDbSessionWithoutApplicationContext, closeDbSessionWithoutApplicationContext
from sqlalchemy import select, or_, func
import decimal
from emailNotification import sendEmail
from messages import getStockNeedsReorderingMessage
from filelock import Timeout, FileLock
from datetime import datetime
from shutil import copy2
from paths import dbBackupStatusFilePath, dbBackupDirPath

bp = Blueprint('backup', __name__)

@bp.route("/initiateBackup", methods=("POST",))
@admin_access_required
def startBackupCommand():
	threading.Thread(target=backUpDatabase).start()
	return make_response("Backup started", 200)


@bp.route("/getBackupStatus")
@admin_access_required
def getBackupStatus():
	attempts = 5
	status = {"isDone": False}
	while (attempts > 0):
		try:
			f = open(dbBackupStatusFilePath, 'r')
			status["statusMessage"] = f.readline()
			f.close()
			if status["statusMessage"] == "Backup Complete":
				status["isDone"] = True
			break
		except IOError:
			time.sleep(1)
			attempts -= 1

	return make_response(status, 200)


def backUpDatabase():
	def updateStatus(StatusString):
		''' Simple function to write status updates to a file '''
		attempts = 5
		while(attempts > 0):
			try:
				f = open(dbBackupStatusFilePath, 'w')
				f.write(StatusString)
				f.close()
				break
			except:
				time.sleep(1)
				attempts -= 1
	'''
	Moves each existing backup up one number, and then copies the existing database to the newly cleared position.
	'''
	updateStatus("Preparing Backup")
	backupFileNames = []
	dbSession = getDbSessionWithoutApplicationContext()
	backupCount = dbSession.query(Settings.dbNumberOfBackups).first()[0]
	closeDbSessionWithoutApplicationContext(dbSession)

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
		updateStatus("Copying")
		now = datetime.now()
		filename = f"inventory_tracker_db_backup_{now.year}-{now.month:0>2}-{now.day:0>2}_{now.hour:0>2}:{now.minute:0>2}:{now.second:0>2}.sqlite"
		backupFilePath = os.path.join(dbBackupDirPath, filename)
		if copy2(dbPath, backupFilePath):
			updateStatus("Backup Complete")
	except Timeout as e:
		updateStatus("Backup Failed")
	except IOError as e:
		updateStatus("Backup Failed")
	finally:
		dbLock.release()



