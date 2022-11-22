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

import decimal
import logging
import os

from flask import (
	Blueprint, request, make_response, jsonify, current_app,
	send_file
)
from sqlalchemy import select, func

from auth import login_required, create_access_required, edit_access_required
from db import getDbSession
from dbSchema import Job, Settings, AssignedStock, CheckInRecord, CheckOutRecord, ProductType, JobTemplate, \
	TemplateStockAssignment, Bin
from qrCodeFunctions import convertDpiAndMmToPx, generateIdCard
from utilities import writeDataToCsvFile

bp = Blueprint('jobs', __name__)


@bp.route("/createJob", methods=("POST",))
@create_access_required
def createJob():
	error = None
	if "jobName" not in request.json:
		error = "jobName must be defined"
	if request.json.get("jobName") == "":
		error = "Job Name must not be blank"

	session = getDbSession()

	if session.query(Job).filter(Job.jobName == request.json['jobName']).first():
		error = "A job with that name exists. Job names must be unique"

	if error:
		return make_response(error, 400)

	job = Job()
	session.add(job)
	session.flush()

	job.idString = f"job_{job.id}"

	error = updateJobFromRequest(job.id, session)
	if error is None:
		session.commit()
		return make_response({"updatedJobId": job.id}, 200)
	else:
		session.rollback()
		return make_response(error, 400)


@bp.route("/updateJob", methods=("POST",))
@edit_access_required
def updateJob():
	error = None
	if "jobId" not in request.json:
		error = "Job ID must be defined"

	if error:
		return make_response(error, 400)

	session = getDbSession()
	error = updateJobFromRequest(request.json["jobId"], session)
	if error is None:
		session.commit()
		return make_response({"updatedJobId": request.json["jobId"]}, 200)
	else:
		session.rollback()
		return make_response(error, 400)


@bp.route("/deleteJob/<jobId>", methods=("POST",))
@create_access_required
def deleteJob(jobId):
	dbSession = getDbSession()

	job = dbSession.query(Job).filter(Job.id == jobId).scalar()
	stockAllocations = dbSession.query(AssignedStock).filter(AssignedStock.associatedJob == jobId).all()
	for stockAllocation in stockAllocations:
		dbSession.delete(stockAllocation)

	if job.qrCodeName:
		qrCodePath = os.path.join(current_app.instance_path, job.qrCodeName)
		if os.path.exists(qrCodePath):
			os.remove(qrCodePath)

	dbSession.delete(job)

	dbSession.commit()

	return make_response("job deleted", 200)


@bp.route("/processJobTemplate", methods=("POST",))
@create_access_required
def processJobTemplate():
	"""
	Create a job template, or update an existing one based on ID
	"""
	dbSession = getDbSession()

	template = dbSession.query(JobTemplate).filter(JobTemplate.id == request.json["templateId"]).first()
	if template is None:
		template = JobTemplate()
		dbSession.add(template)

	template.templateName = request.json["templateName"]
	dbSession.flush()

	existingAssignments = dbSession.query(TemplateStockAssignment).filter(TemplateStockAssignment.jobTemplateId == template.id).all()
	for assignment in existingAssignments:
		dbSession.delete(assignment)

	for row in request.json["templateStockAssignments"]:
		stockAssignment = TemplateStockAssignment(
			jobTemplateId=template.id,
			productId=row["productId"],
			quantity=decimal.Decimal(row["quantity"])
		)
		dbSession.add(stockAssignment)

	dbSession.commit()

	return make_response(jsonify({"templateId": template.id}), 200)


@bp.route("/getTemplateList")
@login_required
def getTemplateList():
	dbSession = getDbSession()
	searchTerm = f"%{request.args.get('searchTerm', default='')}%"

	templates = dbSession.query(JobTemplate) \
		.filter(JobTemplate.templateName.ilike(searchTerm))\
		.order_by(JobTemplate.templateName.asc())\
		.all()
	templateList = [template.toDict() for template in templates]
	return make_response(jsonify(templateList), 200)


@bp.route("/getTemplateStockAssignment")
@login_required
def getTemplateStockAssignment():
	dbSession = getDbSession()

	stockAssignments = dbSession.query(
			ProductType.productName,
			ProductType.id,
			ProductType.quantityUnit,
			TemplateStockAssignment.quantity
		)\
		.join(TemplateStockAssignment)\
		.order_by(ProductType.productName)\
		.all()

	stockAssignmentList = [
			{"productName": row[0], "productId": row[1], "quantityUnit": row[2], "quantity": row[3]} \
			for row in stockAssignments
		]

	return make_response(jsonify(stockAssignmentList), 200)


@bp.route("/deleteTemplate", methods=("POST",))
@create_access_required
def deleteTemplate():
	dbSession = getDbSession()
	templateId = request.args.get("templateId")
	template = dbSession.query(JobTemplate).filter(JobTemplate.id == templateId).one()
	dbSession.query(TemplateStockAssignment)\
		.filter(TemplateStockAssignment.jobTemplateId == templateId)\
		.delete()

	dbSession.delete(template)

	dbSession.commit()

	return make_response("Template deleted", 200)


# process changes from overview page job panel. Encapsulted for reusability
def updateJobFromRequest(jobId, dbSession):
	error = None
	if "jobName" not in request.json:
		error = "jobName must be defined"

	if error:
		return error

	job = dbSession.query(Job).filter(Job.id == jobId).scalar()
	job.jobName = request.json["jobName"]

	if "newStockAssignments" in request.json:
		for i in range(len(request.json['newStockAssignments'])):
			newAssignment = AssignedStock(
				associatedJob=jobId,
				productId=request.json['newStockAssignments'][i]['productId'],
				quantity=decimal.Decimal(request.json['newStockAssignments'][i]['quantity'])
			)
			dbSession.add(newAssignment)

	if "changedStockAssignments" in request.json:
		for i in range(len(request.json['changedStockAssignments'])):
			assignment = dbSession.query(AssignedStock)\
				.filter(AssignedStock.id == request.json['changedStockAssignments'][i]['assignmentId'])\
				.scalar()

			assignment.quantity = decimal.Decimal(request.json['changedStockAssignments'][i]['newQuantity'])

	if "deletedStockAssignments" in request.json:
		for i in range(len(request.json['deletedStockAssignments'])):
			dbSession.query(AssignedStock)\
				.filter(AssignedStock.id == request.json["deletedStockAssignments"][i])\
				.delete()

	job.lastUpdated = func.current_timestamp()

	return None


def generateJobIdQrCodeLabel(QrCodeString, JobName, DbSession):
	cardHeight_mm, cardWidth_mm, cardDpi, cardPadding_mm, showCardName, fontSize = DbSession.query(
		Settings.idCardHeight_mm,
		Settings.idCardWidth_mm,
		Settings.idCardDpi,
		Settings.idCardPadding_mm,
		Settings.displayJobIdCardName,
		Settings.idCardFontSize_px
	).first()

	cardHeightPx = convertDpiAndMmToPx(length_mm=cardHeight_mm, DPI=cardDpi)
	cardWidthPx = convertDpiAndMmToPx(length_mm=cardWidth_mm, DPI=cardDpi)
	cardPaddingPx = convertDpiAndMmToPx(length_mm=cardPadding_mm, DPI=cardDpi)

	if showCardName:
		idCard = generateIdCard(
			idString=QrCodeString,
			totalWidth=cardWidthPx,
			totalHeight=cardHeightPx,
			padding=cardPaddingPx,
			label=JobName,
			labelFontSize=fontSize
		)
	else:
		idCard = generateIdCard(
			idString=QrCodeString,
			totalWidth=cardWidthPx,
			totalHeight=cardHeightPx,
			padding=cardPaddingPx
		)

	return idCard


@bp.route("/getJobs")
@login_required
def getJobs():
	jobList = getJobsDataFromRequest()
	return make_response(jsonify(jobList), 200)


def getJobsDataFromRequest():
	session = getDbSession()
	stmt = select(Job)
	if "searchTerm" in request.args:
		searchTerm = "%" + request.args.get("searchTerm") + "%"
		stmt = stmt.where(Job.jobName.ilike(searchTerm))

	if request.args.get("orderByName", type=bool, default=False):
		stmt = stmt.order_by(Job.jobName.asc())
	elif request.args.get("orderByDateAdded", type=bool, default=False):
		stmt = stmt.order_by(Job.addedTimestamp.asc())
	else:
		stmt = stmt.order_by(Job.jobName.asc())

	jobs = session.execute(stmt).scalars().all()
	# the jobList also needs the current total cost of the job. This is calculated and added to the dict that represents
	# the rest of the job's details.
	jobList = []
	for job in jobs:
		stock, totalCost = getTotalStockUsedOnJob(job)  # note stock is unused here
		d = job.toDict()
		d['totalCost'] = totalCost
		jobList.append(d)

	session.close()
	return jobList


@bp.route("/getJob")
@login_required
def getJob():
	session = getDbSession()
	jobId = request.args.get("jobId")
	job = session.query(Job).filter(Job.id == jobId).scalar()
	if job is None:
		return make_response("No such job", 404)

	assignedStockResult = session.query(AssignedStock.id, AssignedStock.quantity, ProductType.productName, ProductType.quantityUnit)\
		.filter(AssignedStock.associatedJob == job.id)\
		.join(ProductType, AssignedStock.productId == ProductType.id)\
		.order_by(ProductType.productName)\
		.all()
	assignedStockList = [
		{
			"productName": row[2],
			"assignationId": row[0],
			"quantity": row[1],
			"unit": row[3]
		}
		for row in assignedStockResult
	]

	stockUsedTotals, stockUsedTotalCost = getTotalStockUsedOnJob(job)

	# order stockTotalsUsed lists alphabetically by product type name
	keys = sorted(stockUsedTotals.keys())
	stockUsedList = [stockUsedTotals[key] for key in keys]

	jobDataDict = job.toDict()
	jobDataDict.update({"assignedStock": assignedStockList, "stockTotals": stockUsedList, "cost": stockUsedTotalCost})
	return jsonify(jobDataDict)


def getTotalStockUsedOnJob(job):
	# the stock used is calculated as the total checked out for each item minus the total checked in.
	dbSession = getDbSession()
	stockUsedTotals = {}
	totalCost = decimal.Decimal()
	# get total checked out first, per product
	checkOutRecords = dbSession.query(CheckOutRecord).filter(CheckOutRecord.jobId == job.id).all()
	for checkOutRecord in checkOutRecords:
		productType = checkOutRecord.associatedStockItem.associatedProduct

		if productType.productName not in stockUsedTotals:
			stockUsedTotals[productType.productName] = {
				'productName': productType.productName,
				'productId': checkOutRecord.associatedStockItem.associatedProduct.id,
				'qtyOfProductUsed': decimal.Decimal(),
				'costOfProductUsed': decimal.Decimal(),
				'quantityUnit': productType.quantityUnit
			}

		stockUsedTotals[productType.productName]['qtyOfProductUsed'] += checkOutRecord.quantity
		stockUsedTotals[productType.productName]['costOfProductUsed'] += \
			(checkOutRecord.quantity / productType.initialQuantity) * checkOutRecord.associatedStockItem.price

		totalCost += (checkOutRecord.quantity / productType.initialQuantity)\
					 * checkOutRecord.associatedStockItem.price

	# then subtract what was checked back in
	checkInRecords = dbSession.query(CheckInRecord).filter(CheckInRecord.jobId == job.id).all()
	for checkInRecord in checkInRecords:
		productTypeName = checkInRecord.associatedStockItem.associatedProduct.productName

		if productTypeName not in stockUsedTotals:
			logging.warning(
				f"A check-in record associated with stockItem {checkInRecord.stockItem} and job {job.id}, "
				f"but none of this product type was recorded as being checked out"
			)
			continue

		stockUsedTotals[productTypeName]['qtyOfProductUsed'] -= checkInRecord.quantity
		stockUsedTotals[productTypeName]['costOfProductUsed'] -= \
			(checkInRecord.quantity / productType.initialQuantity) * checkInRecord.associatedStockItem.price

		totalCost -= (checkInRecord.quantity / productType.initialQuantity) * checkInRecord.associatedStockItem.price

	for key in stockUsedTotals.keys():
		stockUsedTotals[key]['costOfProductUsed'] = round(stockUsedTotals[key]['costOfProductUsed'], 2)

	totalCost = round(totalCost, 2)
	return stockUsedTotals, totalCost


@bp.route("/addAssignedStock", methods=("POST",))
@edit_access_required
def addAssignedStock():
	error = None
	if "productId" not in request.form:
		error = "productId must be defined"
	if "quantity" not in request.form:
		error = "quantity must be defined"
	if "jobId" not in request.form:
		error = "jobId must be defined"
	if error:
		return make_response(error, 400)

	session = getDbSession()
	newAssignedStock = AssignedStock(
		productId=request.form['productId'],
		quantity=request.form['quantity'],
		associatedJob=request.form['jobId']
	)
	session.add(newAssignedStock)
	session.commit()
	session.close()

	return make_response("Item added", 200)


@bp.route("/deleteAssignedStock", methods=("POST",))
@edit_access_required
def deleteAssignedStock():
	if "assignedItemId" not in request.form and "assignedItemList" not in request.form:
		return make_response("Item ID or ID list must be provided")

	if "assignedItemId" in request.form:
		idList = [request.form['assignedItemId']]
	else:
		idList = request.form['assignedItemList']

	session = getDbSession()
	for itemId in idList:
		session.query(AssignedStock).filter(AssignedStock.id == itemId).scalar().delete()

	return make_response("Items deleted", 200)


@bp.route("/getJobsCsvFile", methods=("GET",))
@login_required
def getJobsCsvFile():
	jobsData = getJobsDataFromRequest()
	headingDictList = [
		{"heading": "Job Name", "dataName": "jobName"},
		{"heading": "Created Timestamp", "dataName": "addedTimestamp"},
		{"heading": "Cumulative Cost", "dataName": "totalCost"},

	]
	csvPath = writeDataToCsvFile(headingsDictList=headingDictList, dataDictList=jobsData)

	return send_file(csvPath, as_attachment=True, download_name="jobsInfo.csv", mimetype="text/csv")

@bp.route("/getPickingList")
@login_required
def getPickingList():
	'''
	this can probably be improved, but it'll do for now
	produces a simple text file. works to a maximum width of 80 characters

	format of the file is

	Picking list for <job name>

	qty.        product name    barcode             bin
	<qty> x     <product name>  <product barcode>   <some location>
	<qty> x     <product name>  <product barcode>   <some location>

	'''

	pageWidth = 80
	padWidth = 3
	quantityWidth = 6
	barcodeWidth = 16
	binWidth = 20
	# special as likely widest
	productNameWidth = pageWidth - ((padWidth * 3) + quantityWidth + barcodeWidth + binWidth)

	padChar = " "
	quantityLabel = "Qty."
	barcodeLabel = "Barcode"
	binLabel = "Bin (last seen)"
	productNameLabel = "Product Name"


	dbSession = getDbSession()
	jobId = request.args.get("jobId", default=None)
	if jobId is None:
		return make_response("jobId is required", 400)

	pickingListDescription = []

	job = dbSession.query(Job).filter(Job.id == jobId).first()

	assignedStockRecords = dbSession.query(AssignedStock)\
		.filter(AssignedStock.associatedJob == jobId)\
		.order_by(AssignedStock.id)\
		.all()

	for assignedStockRecord in assignedStockRecords:
		product = dbSession.query(ProductType).filter(ProductType.id == assignedStockRecord.productId).one()
		lastCheckInRecord = dbSession.query(CheckInRecord).filter(CheckInRecord.productType == product.id).order_by(CheckInRecord.timestamp).first()

		binName = "Location not recorded"
		if lastCheckInRecord:
			bin = dbSession.query(Bin).filter(Bin.id == lastCheckInRecord.binId).first()
			if bin is not None:
				binName = bin.locationName

		rowDescription = {
			"productName": product.productName,
			"quantity": assignedStockRecord.quantity,
			"binName": binName,
			"barcode": product.barcode
		}

		pickingListDescription.append(rowDescription)

	# generate file
	filepath = os.path.join(current_app.instance_path, "pickingListFile.txt")
	pickingListFile = open(filepath, "w")
	pickingListFile.write(f"Picking List for {job.jobName}\n\n")
	pickingListFile.write(
		f"{quantityLabel:<{quantityWidth}}{padChar:{padWidth}}{productNameLabel:<{productNameWidth}}"
		f"{padChar:{padWidth}}{barcodeLabel:<{barcodeWidth}}{padChar:{padWidth}}{binLabel:<{binWidth}}\n\n")

	for row in pickingListDescription:
		pickingListFile.write(
			f"{row['quantity']:<{quantityWidth}}{padChar:{padWidth}}{row['productName']:<{productNameWidth}}"
			f"{padChar:{padWidth}}{row['barcode']:<{barcodeWidth}}{padChar:{padWidth}}{row['binName']:<{binWidth}}\n\n")

	pickingListFile.close()

	return send_file(filepath, as_attachment=True, download_name=f"Picking List {job.jobName}.txt")


@bp.route("/getJobLastUpdateTimestamp")
@login_required
def getJobLastUpdateTimestamp():
	itemId = request.args.get("itemId")
	dbSession = getDbSession()
	item = dbSession.query(Job).filter(Job.id == itemId).one()
	timestamp = item.lastUpdated.strftime("%d/%m/%y %H:%M:%S")
	return make_response(timestamp, 200)


@bp.route("/getJobIdCard")
@login_required
def getJobIdCard():
	dbSession = getDbSession()
	jobId = request.args.get("jobId", default=None)
	if jobId is None:
		return make_response("jobId must be provided", 400)
	job = dbSession.query(Job).filter(Job.id == jobId).first()
	qrCodePath = os.path.join(current_app.instance_path, "jobIdCard.png")
	idCard = generateIdCard(idString=job.idString, label=job.jobName, labelFontSize=30, totalWidth=400, totalHeight=200)

	idCard.save(qrCodePath)

	return send_file(qrCodePath, as_attachment=True, download_name=f"{job.jobName}_id_card.png")
