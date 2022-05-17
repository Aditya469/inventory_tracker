import functools
import os
from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for, request, make_response, jsonify,current_app
)
from sqlalchemy import select
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from db import getDbSession
from dbSchema import Job, Settings, AssignedStock
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
	job.jobName = request.form.get("jobName")
	session.flush()

	qrCodeString = f"job_{job.id}"
	job.qrCodePath = os.path.join(current_app.instance_path, qrCodeString + ".png")

	cardHeight_mm, cardWidth_mm, cardDpi, cardPadding_mm, showCardName, fontSize = session.query(
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
			idString=qrCodeString,
			totalWidth=cardWidthPx,
			totalHeight=cardHeightPx,
			padding=cardPaddingPx,
			label=job.jobName,
			labelFontSize=fontSize
		)
	else:
		idCard = generateIdCard(
			idString=qrCodeString,
			totalWidth=cardWidthPx,
			totalHeight=cardHeightPx,
			padding=cardPaddingPx
		)

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


@bp.route("/getJobs")
@login_required
def getJobs():
	session = getDbSession()
	stmt = select(Job)
	if "searchPhrase" in request.args:
		searchTerm = "%" + request.args.get("searchPhrase") + "%"
		stmt = stmt.where(Job.jobName.ilike(searchTerm))

	if request.args.get("orderByName", type=bool, default=False):
		stmt = stmt.order_by(Job.jobName.asc())
	elif request.args.get("orderByDateAdded", type=bool, default=False):
		stmt = stmt.order_by(Job.addedTimestamp.asc())
	else:
		stmt = stmt.order_by(Job.jobName.asc())

	jobs = session.execute(stmt)
	jobList = [job.toDict for job in jobs]
	session.close()
	return make_response(jsonify(jobList),  200)
