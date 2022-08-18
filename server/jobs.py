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
	if "jobName" not in request.json:
		error = "Job Name must be defined"

	session = getDbSession()

	if session.query(Job).filter(Job.jobName == request.json['jobName']).first():
		error = "A job with that name exists. Job names must be unique"

	if error:
		return make_response(error, 400)

	job = Job()
	session.add(job)
	session.flush()

	job.idString = f"job_{job.id}"
	job.qrCodeName = job.idString + ".png"
	qrCodePath = os.path.join(current_app.instance_path, job.qrCodeName)
	idCard = generateJobIdQrCodeLabel(QrCodeString=job.idString, JobName=request.json['jobName'], DbSession=session)
	idCard.save(qrCodePath)

	error = updateJobFromRequest(job.id, session)
	if error is None:
		session.commit()
		return make_response({"newJobId": job.id}, 200)
	else:
		session.rollback()
		return make_response(error, 400)


@bp.route("/updateJob", methods=("POST",))
@login_required
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
		return make_response("Changes Saved", 200)
	else:
		session.rollback()
		return make_response(error, 400)


@bp.route("/deleteJob/<jobId>", methods=("POST",))
@login_required
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


# process changes from overview page job panel. Encapsulted for reusability
def updateJobFromRequest(jobId, dbSession):
	error = None
	if "jobName" not in request.json:
		error = "jobName must be defined"

	if error:
		return error

	job = dbSession.query(Job).filter(Job.id == jobId).scalar()
	job.jobName = request.json["jobName"];

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


@bp.route("/getJob/<jobId>")
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
	stockUsedTotals = {}
	totalCost = decimal.Decimal()
	# get total checked out first, per product
	for checkOutRecord in job.associatedStockCheckouts:
		productType = checkOutRecord.associatedStockItem.associatedProduct

		if productType.productName not in stockUsedTotals:
			stockUsedTotals[productType.productName] = {
				'productName': productType.productName,
				'productId': checkOutRecord.associatedStockItem.associatedProduct.id,
				'qtyOfProductUsed': decimal.Decimal(),
				'costOfProductUsed': decimal.Decimal(),
				'quantityUnit': productType.quantityUnit
			}

		stockUsedTotals[productType.productName]['qtyOfProductUsed'] += checkOutRecord.quantityCheckedOut
		stockUsedTotals[productType.productName]['costOfProductUsed'] += \
			(checkOutRecord.quantityCheckedOut / productType.initialQuantity) * checkOutRecord.associatedStockItem.price

		totalCost += (checkOutRecord.quantityCheckedOut / productType.initialQuantity)\
					 * checkOutRecord.associatedStockItem.price

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
			(checkInRecord.quantityCheckedIn / productType.initialQuantity) * checkInRecord.associatedStockItem.price

		totalCost -= (checkInRecord.quantityCheckedIn / productType.initialQuantity) * checkInRecord.associatedStockItem.price

	for key in stockUsedTotals.keys():
		stockUsedTotals[key]['costOfProductUsed'] = round(stockUsedTotals[key]['costOfProductUsed'], 2)

	totalCost = round(totalCost, 2)
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
	for itemId in idList:
		session.query(AssignedStock).filter(AssignedStock.id == itemId).scalar().delete()

	return make_response("Items deleted", 200)

