import decimal
import functools
import logging
import os
from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, request, make_response, jsonify,current_app
)
from sqlalchemy import select, func
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from db import getDbSession
from dbSchema import Job, Settings, AssignedStock, CheckInRecord, CheckOutRecord, ProductType
import json
from auth import login_required
from qrCodeFunctions import convertDpiAndMmToPx, generateIdCard
bp = Blueprint('jobs', __name__)


@bp.route("/createJob", methods=("POST",))
@login_required
def createJob():
	error = None
	if "jobName" not in request.form:
		error = "Job Name must be defined"

	if error:
		return make_response(error, 400)

	session = getDbSession()

	job = Job()
	session.add(job)
	job.jobName = request.form.get("jobName")
	session.flush()

	qrCodeString = f"job_{job.id}"
	job.qrCodePath = os.path.join(current_app.instance_path, qrCodeString + ".png")
	idCard = generateJobIdQrCodeLabel(QrCodeString=qrCodeString, JobName=job.jobName, DbSession=session)
	idCard.save(job.qrCodePath)

	reqStockList = request.form.get("requiredStockList", default=None)
	if reqStockList:
		reqStockListJson = json.loads(reqStockList)
		for stockReq in reqStockListJson:
			assignedStockEntry = AssignedStock()
			assignedStockEntry.productId = stockReq["productTypeId"]
			assignedStockEntry.quantity = stockReq["quantityrequired"]
			session.add(assignedStockEntry)

	session.commit()
	session.close()

	return make_response(f"{request.form.get('jobName')} added", 200)


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
	return make_response(jsonify(jobList),  200)


@bp.route("/getJob/<int:jobId>")
@login_required
def getJob(jobId):
	session = getDbSession()
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
			"AssignationId": row[0],
			"quantity": row[1],
			"unit": row[3]
		}
		for row in assignedStockResult
	]

	stockUsedTotals, stockUsedTotalCost = getTotalStockUsedOnJob(job)

	# order stockTotalsUsed lists alphabetically by product type name
	keys = sorted(stockUsedTotals.keys())
	stockUsedList = [stockUsedTotals[key] for key in keys]

	return jsonify({"assignedStock": assignedStockList, "stockTotals": stockUsedList, "cost": stockUsedTotalCost})
	return render_template(
		"jobDetails",
		jobId=jobId,
		assignedStock=assignedStockList,
		usedStock=stockUsedList,
		totalCost=stockUsedTotalCost
	)


def getTotalStockUsedOnJob(job):
	# the stock used is calculated as the total checked out for each item minus the total checked in.
	stockUsedTotals = {}
	totalCost = decimal.Decimal()
	# get total checked out first, per product
	for checkOutRecord in job.associatedStockCheckouts:
		productTypeName = checkOutRecord.associatedStockItem.associatedProduct.productName

		if productTypeName not in stockUsedTotals:
			stockUsedTotals[productTypeName] = {
				'productName': productTypeName,
				'productId': checkOutRecord.associatedStockItem.associatedProduct.id,
				'qtyOfProductUsed': decimal.Decimal(),
				'costOfProductUsed': decimal.Decimal()
			}

		stockUsedTotals[productTypeName]['qtyOfProductUsed'] += checkOutRecord.quantityCheckedOut
		stockUsedTotals[productTypeName]['costOfProductUsed'] += \
			checkOutRecord.quantityCheckedOut * checkOutRecord.associatedStockItem.price

		totalCost += checkOutRecord.quantityCheckedOut * checkOutRecord.associatedStockItem.price

	# then subtract what was checked back in
	for checkInRecord in job.associatedStockCheckins:
		productTypeName = checkInRecord.associatedStockItem.associatedProduct.productName

		if productTypeName not in stockUsedTotals:
			logging.warning(
				f"A check-in record associated with stockItem {checkInRecord.stockItem} and job {job.id}, "
				f"but none of this product type was recorded as being checked out"
			)
			continue

		stockUsedTotals[productTypeName]['qtyOfProductUsed'] -= checkInRecord.quantityCheckedIn
		stockUsedTotals[productTypeName]['costOfProductUsed'] -= \
			checkInRecord.quantityCheckedIn * checkInRecord.associatedStockItem.price

		totalCost -= checkInRecord.quantityCheckedIn * checkInRecord.associatedStockItem.price

	return stockUsedTotals, totalCost


@bp.route("/addAssignedStock", methods=("POST",))
@login_required
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
@login_required
def deleteAssignedStock():
	if "assignedItemId" not in request.form and "assignedItemList" not in request.form:
		return make_response("Item ID or ID list must be provided")

	if "assignedItemId" in request.form:
		idList = [request.form['assignedItemId']]
	else:
		idList = request.form['assignedItemList']

	session = getDbSession()
	for id in idList:
		session.query(AssignedStock).filter(AssignedStock.id == id).scalar().delete()

	return make_response("Items deleted", 200)

