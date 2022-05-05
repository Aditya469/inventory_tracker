import math

from PIL import Image, ImageDraw, ImageFont
from flask import current_app
import qrcode
import os
from .db import getDbSession, ItemId


def fetchAvailableItemIds(countRequired):
	dbSession = getDbSession()

	countToCreate = countRequired - dbSession \
		.query(ItemId).filter(ItemId.isAssigned is False).filter(ItemId.isAssigned is False).count()

	for i in range(countToCreate):
		newId = ItemId()
		dbSession.add(newId)

	dbSession.commit()

	availableIds = dbSession\
		.query(ItemId)\
		.filter(ItemId.isPendingAssignment)\
		.order_by(ItemId.idNumber.desc())\
		.limit(countRequired)\
		.all()

	return availableIds


def generateIdQCode(idString, label=None, labelFontSize=12, totalWidth=200, totalHeight=100, padding=10):
	qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
	qr.add_data(idString)
	qr.make(fit=True)
	qrImg = qr.make_image()
	finalImg = qrImg

	# note, assumes that the label will not occupy more than half the total width and can be one line
	if label is not None:
		img = Image.new("RGB", (totalWidth, totalHeight), (255, 255, 255))
		font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", labelFontSize)
		d = ImageDraw.Draw(img)
		d.text((10+padding, totalHeight/2), label, font=font, fill=(0, 0, 0))
		qrDim = min(math.floor(totalWidth/2) - padding, totalHeight - (2 * padding))
		qrImg = qrImg.resize((qrDim, qrDim))
		img.paste(qrImg, (math.floor(totalWidth/2), padding))
		finalImg = img

	return finalImg


def createImageSheet(fileNames, totalWidthPx, totalHeightPx, arrayWidthPx, arrayHeightPx, rows, cols):
	if len(fileNames) > rows * cols:
		raise Exception("filename count exceeds row * column count")
	if arrayWidthPx > totalWidthPx:
		raise Exception("array width must not exceed total width")
	if arrayHeightPx > totalHeightPx:
		raise Exception("array height must not exceed total height")

	rowStep = arrayHeightPx / rows
	rowOffset = (0.5 * rowStep) + (0.5 * (totalHeightPx - arrayHeightPx))

	colStep = arrayWidthPx / cols
	colOffset = (0.5 * colStep) + (0.5 * (totalWidthPx - arrayWidthPx))

	mainImg = Image.new('RGB', (totalWidthPx, totalHeightPx))
	mainImg.paste((255, 255, 255), [0, 0, totalWidthPx, totalHeightPx])

	rowIndex = 0
	colIndex = 0
	# open each image. if larger than the row or column step, shrink to fit.
	# paste into the main image
	for file in fileNames:
		img = Image.open(file)
		imgWidth, imgHeight = img.size
		if imgWidth > colStep or imgHeight > rowStep:
			heightScaleFactor = rowStep / imgHeight
			widthScaleFactor = colStep / imgWidth
			scaleFactor = min(widthScaleFactor, heightScaleFactor)
			newSize = (math.floor(imgWidth * scaleFactor), math.floor(imgHeight * scaleFactor))
			img = img.resize(newSize)
			imgWidth, imgHeight = img.size

		topleftCoord = (
			math.floor((colOffset + (colStep * colIndex)) - (0.5 * imgWidth)),
			math.floor((rowOffset + (rowStep * rowIndex)) - (0.5 * imgHeight))
		)
		mainImg.paste(img, topleftCoord)

		colIndex += 1
		if colIndex == cols:
			colIndex = 0
			rowIndex += 1

	return mainImg


def generateItemIdQrCodeSheets(
		idCount, rows, columns, pageWidth, pageHeight, arrayWidth, arrayHeight, stickerPadding, includeLabels=True):
	# get a list of IDs
	idList = fetchAvailableItemIds(idCount)
	fileList = []
	# generate image of required page(s) based on settings
	for id in idList:
		idCard = generateIdQCode(
			idString=f"{id.idNumber}",
			label=f"Item ID {id.idNumber}",
			labelFontSize=40,
			totalWidth=math.floor(arrayWidth/columns),
			totalHeight=math.floor(arrayHeight/rows),
			padding=stickerPadding
		)
		filename = f"{current_app.instance_path}/{id.idNumber}.png"
		idCard.save(filename)
		fileList.append(filename)

	labelSheets = []
	step = rows * columns
	for i in range(math.ceil(len(fileList) / step)):
		labelSheets.append(
			createImageSheet(
				fileNames=fileList[i * step:i + 1 * step],
				rows=rows,
				cols=columns,
				totalWidthPx=pageWidth,
				totalHeightPx=pageHeight,
				arrayWidthPx=arrayWidth,
				arrayHeightPx=arrayHeight
			)
		)

	for i in range(len(fileList)):
		os.remove(fileList[i])

	return labelSheets

def convertDpiAndMmToPx(length_mm, DPI):
	return round((DPI * length_mm) / 25.4)
