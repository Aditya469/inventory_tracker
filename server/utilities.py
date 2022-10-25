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

import csv
import os

from flask import current_app

'''
	headingDictList -> [{"heading": "<Heading name pretty>", "dataName": "<data key>"}, ...]
	dataDictList -> [{"<data key 1">: <data value 1>, "<data key 2">: <data value 2>,...}, {"<data key 1">: <data value 1>, "<data key 2">: <data value 2>,...}]  
'''
def writeDataToCsvFile(headingsDictList, dataDictList, filename="tempCsvFile.csv", delimiter=','):
	path = os.path.join(current_app.instance_path, filename)
	with open(path, "w") as csvFile:
		csvWriter = csv.writer(csvFile, delimiter=delimiter)
		csvWriter.writerow([headingDict["heading"] for headingDict in headingsDictList])
		for row in dataDictList:
			rowList = ["{}".format(row[headingDict["dataName"]]) for headingDict in headingsDictList]

			csvWriter.writerow(rowList)

	return path


def formatStockAmount(stockAmount, maxDecimalPlaces):
	if int(stockAmount) != stockAmount:
		stockAmount = round(stockAmount, maxDecimalPlaces)

	return f"{stockAmount}"


