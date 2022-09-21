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
import datetime
import time

from apscheduler.schedulers.background import BackgroundScheduler

from backup import backUpDatabase
from db import getDbSessionWithoutApplicationContext, closeDbSessionWithoutApplicationContext
from dbSchema import Settings


def setUpScheduler():
	'''
	The scheduled task runs every 60 seconds and executes tasks if the current time (HH:MM) matches the
	time specified in the settings.
	'''
	scheduler = BackgroundScheduler()
	scheduler.start()
	#scheduler.add_job(findAndRunScheduledTasks, 'interval', seconds=60)
	scheduler.add_job(findAndRunScheduledTasks, 'date')
	return scheduler


def findAndRunScheduledTasks():
	print("Looking for scheduled tasks")
	session = getDbSessionWithoutApplicationContext()
	settings = session.query(Settings).first()
	currentTimeFull = datetime.datetime.now().time()
	currentTimeTrunc = datetime.time(hour=currentTimeFull.hour, minute=currentTimeFull.minute)

	# since some tasks require the DB to be locked, this function compiles a list of tasks to run
	# and then runs them
	runDbBackup = False

	# DB backup
	if settings.dbBackupAtTime == currentTimeTrunc:
		runDbBackup = True

	# other tasks go here...

	closeDbSessionWithoutApplicationContext(session)

	# npw start running tasks
	if runDbBackup:
		backUpDatabase()


def main():
	scheduler = setUpScheduler()

	while(True):
		time.sleep(1)


if __name__ == "__main__":
	main()
