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
import datetime
import logging
import sys
import time
import paths

from apscheduler.schedulers.background import BackgroundScheduler

from __init__ import app
import paths
from backup import backUpDatabase
from db import getDbSession, close_db
from dbSchema import Settings
from productManagement import performStockCheckAndReport


def setUpScheduler():
	'''
	The scheduled task runs every 60 seconds and executes tasks if the current time (HH:MM) matches the
	time specified in the settings.
	'''
	scheduler = BackgroundScheduler()
	scheduler.start()
	logging.info("Created background scheduler")
	scheduler.add_job(findAndRunScheduledTasks, 'interval', seconds=60)
	logging.info("Added job to run database scheduled tasks")
	return scheduler


def findAndRunScheduledTasks():
	logging.debug("Running findAndRunScheduledTasks")
	with app.app_context():
		session = getDbSession()
		settings = session.query(Settings).first()
		currentTimeFull = datetime.datetime.now().time()
		currentTimeTrunc = datetime.time(hour=currentTimeFull.hour, minute=currentTimeFull.minute)
		currentDayOfWeek = datetime.datetime.now().weekday()

		# since some tasks require the DB to be locked, this function compiles a list of tasks to run
		# and then runs them
		functionsToBeRun = []

		# DB backup
		if settings.dbBackupAtTime == currentTimeTrunc \
				and ((settings.dbBackupOnMonday and currentDayOfWeek == 0)
					 or (settings.dbBackupOnTuesday and currentDayOfWeek == 1)
					 or (settings.dbBackupOnWednesday and currentDayOfWeek == 2)
					 or (settings.dbBackupOnThursday and currentDayOfWeek == 3)
					 or (settings.dbBackupOnFriday and currentDayOfWeek == 4)
					 or (settings.dbBackupOnSaturday and currentDayOfWeek == 5)
					 or (settings.dbBackupOnSunday and currentDayOfWeek == 6)):
			logging.info("Database backup needs to be run")
			functionsToBeRun.append(backUpDatabase)

		if settings.stockLevelReorderCheckAtTime == currentTimeTrunc \
				and ((settings.stockCheckOnMonday and currentDayOfWeek == 0)
					 or (settings.stockCheckOnTuesday and currentDayOfWeek == 1)
					 or (settings.stockCheckOnWednesday and currentDayOfWeek == 2)
					 or (settings.stockCheckOnThursday and currentDayOfWeek == 3)
					 or (settings.stockCheckOnFriday and currentDayOfWeek == 4)
					 or (settings.stockCheckOnSaturday and currentDayOfWeek == 5)
					 or (settings.stockCheckOnSunday and currentDayOfWeek == 6)):
			logging.info("Database stock level reorder check needs to be run")
			functionsToBeRun.append(performStockCheckAndReport)

		# other tasks go here...

		close_db()

		# now start running tasks
		for i in range(len(functionsToBeRun)):
			functionsToBeRun[i]()
			time.sleep(10)  # a short sleep here is to allow any email notifications to be sent. This is decidedly
	# a bodge, but it'll do as a quick fix. TODO: revisit


def main():
	scheduler = setUpScheduler()

	while (True):
		time.sleep(1)


if __name__ == "__main__":
	main()
