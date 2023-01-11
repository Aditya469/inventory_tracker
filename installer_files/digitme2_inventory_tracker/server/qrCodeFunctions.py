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

import math
import os

import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import current_app

from db import getDbSession
from dbSchema import ItemId, Settings


def fetchAvailableItemIds(countRequired):
	dbSession = getDbSession()

	countToCreate = countRequired - dbSession \
		.query(ItemId).filter(ItemId.isPendingAssignment == False, ItemId.isAssigned == False).count()

	for i in range(countToCreate):
		newId = ItemId()
		dbSession.add(newId)
		dbSession.flush()
		newId.idString = f"item_{newId.idNumber}"

	dbSession.commit()

	availableIds = dbSession\
		.query(ItemId)\
		.filter(ItemId.isPendingAssignment == False)\
		.filter(ItemId.isAssigned == False)\
		.order_by(ItemId.idNumber.desc())\
		.limit(countRequired)\
		.all()

	return availableIds


def generateIdCard(idString, label=None, labelFontSize=12, totalWidth=200, totalHeight=100, padding=10):
	qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
	qr.add_data(idString)
	qr.make(fit=True)
	qrImg = qr.make_image()
	finalImg = qrImg

	# place the QR code on the right side of the image, and then attempt to place text. The width of the text is
	# estimated and wrapped if necessary
	if label is not None:
		img = Image.new("RGB", (totalWidth, totalHeight), (255, 255, 255))

		qrDimension = min(math.floor(totalWidth/2) - padding, totalHeight - (2 * padding))
		qrImg = qrImg.resize((qrDimension, qrDimension))
		qrImgLeftPos = totalWidth - (qrDimension + padding)
		qrImgTopPos = padding
		img.paste(qrImg, (qrImgLeftPos, qrImgTopPos))

		font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", labelFontSize)

		textWidth = font.getlength(label)
		availableSpace = qrImgLeftPos - padding
		formattedText = ""
		# if the label needs to be wrapped, attempt to find whitespace to replace with newlines
		if textWidth > availableSpace:
			textChars = []
			lineLength = 0
			lastWhitespaceInTextChars = -1
			for i in range(len(label)):
				lineLength += font.getlength(label[i])
				if lineLength >= availableSpace:
					if lastWhitespaceInTextChars != -1:
						textChars[lastWhitespaceInTextChars] = '\n'
						lastWhitespaceInTextChars = -1
					else:
						textChars.append('\n')
					lineLength = 0
				if label[i] == ' ':
					lastWhitespaceInTextChars = len(textChars)
				textChars.append(label[i])
			formattedText = "".join(textChars)
		else:
			formattedText = label

		textSize = font.getbbox(formattedText)
		textHeight = textSize[3] - textSize[1]
		textTop = (totalHeight / 2) - (textHeight / 2)
		textLeft = padding

		d = ImageDraw.Draw(img)
		d.text((textLeft, textTop), formattedText, font=font, fill=(0, 0, 0))

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


def generateItemIdQrCodeSheets(idCount, includeLabels=True):
	session = getDbSession()
	pageWidth_mm = session.query(Settings.stickerSheetPageWidth_mm).first()[0]
	pageHeight_mm = session.query(Settings.stickerSheetPageHeight_mm).first()[0]
	stickerAreaWidth_mm = session.query(Settings.stickerSheetStickersWidth_mm).first()[0]
	stickerAreaHeight_mm = session.query(Settings.stickerSheetStickersHeight_mm).first()[0]
	stickerPadding_mm = session.query(Settings.stickerPadding_mm).first()[0]
	stickerSheetDpi = session.query(Settings.stickerSheetDpi).first()[0]

	pageWidth = convertDpiAndMmToPx(length_mm=pageWidth_mm, DPI=stickerSheetDpi)
	pageHeight = convertDpiAndMmToPx(length_mm=pageHeight_mm, DPI=stickerSheetDpi)
	arrayWidth = convertDpiAndMmToPx(length_mm=stickerAreaWidth_mm, DPI=stickerSheetDpi)
	arrayHeight = convertDpiAndMmToPx(length_mm=stickerAreaHeight_mm, DPI=stickerSheetDpi)
	stickerPadding = convertDpiAndMmToPx(length_mm=stickerPadding_mm, DPI=stickerSheetDpi)

	rows = session.query(Settings.stickerSheetRows).first()[0]
	columns = session.query(Settings.stickerSheetColumns).first()[0]

	if idCount is None:
		idCount = rows * columns

	# temporary limitation until I find a suitable python pdf library
		if idCount > rows * columns:
			return None, f"You may only request up to {rows * columns} at a time"

	# get a list of IDs
	idList = fetchAvailableItemIds(idCount)
	fileList = []
	# generate image of required page(s) based on settings
	for id in idList:
		id.isPendingAssignment = True
		session.add(id)
		idCard = generateIdCard(
			idString=f"{id.idString}",
			label=f"{id.idString}",
			labelFontSize=25,
			totalWidth=math.floor(arrayWidth/columns),
			totalHeight=math.floor(arrayHeight/rows),
			padding=stickerPadding
		)
		filename = f"{current_app.instance_path}/{id.idString}.png"
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

	session.commit()

	return labelSheets, None

def generateIdQrCodeSheets(idCount, idCardString, includeLabels=True):
	session = getDbSession()
	pageWidth_mm = session.query(Settings.stickerSheetPageWidth_mm).first()[0]
	pageHeight_mm = session.query(Settings.stickerSheetPageHeight_mm).first()[0]
	stickerAreaWidth_mm = session.query(Settings.stickerSheetStickersWidth_mm).first()[0]
	stickerAreaHeight_mm = session.query(Settings.stickerSheetStickersHeight_mm).first()[0]
	stickerPadding_mm = session.query(Settings.stickerPadding_mm).first()[0]
	stickerSheetDpi = session.query(Settings.stickerSheetDpi).first()[0]

	pageWidth = convertDpiAndMmToPx(length_mm=pageWidth_mm, DPI=stickerSheetDpi)
	pageHeight = convertDpiAndMmToPx(length_mm=pageHeight_mm, DPI=stickerSheetDpi)
	arrayWidth = convertDpiAndMmToPx(length_mm=stickerAreaWidth_mm, DPI=stickerSheetDpi)
	arrayHeight = convertDpiAndMmToPx(length_mm=stickerAreaHeight_mm, DPI=stickerSheetDpi)
	stickerPadding = convertDpiAndMmToPx(length_mm=stickerPadding_mm, DPI=stickerSheetDpi)

	rows = session.query(Settings.stickerSheetRows).first()[0]
	columns = session.query(Settings.stickerSheetColumns).first()[0]

	if idCount is None:
		idCount = rows * columns

	# temporary limitation until I find a suitable python pdf library
		if idCount > rows * columns:
			return None, f"You may only request up to {rows * columns} at a time"

	idCard = generateIdCard(
			idString=idCardString,
			label=idCardString,
			labelFontSize=40,
			totalWidth=math.floor(arrayWidth/columns),
			totalHeight=math.floor(arrayHeight/rows),
			padding=stickerPadding
		)
	filename = f"{current_app.instance_path}/productIdCard.png"
	idCard.save(filename)

	# note: quick adaptation of existing code, so works in a weird way. createImageSheet expects a list of file names.
	# Just give it the same name over and over for now.
	fileList = []
	for i in range(idCount):
		fileList.append(filename)
	labelSheets = []
	step = rows * columns
	for i in range(math.ceil(len(fileList) / step)):
		labelSheets.append(
			createImageSheet(
				fileNames=fileList,
				rows=rows,
				cols=columns,
				totalWidthPx=pageWidth,
				totalHeightPx=pageHeight,
				arrayWidthPx=arrayWidth,
				arrayHeightPx=arrayHeight
			)
		)

	session.commit()

	return labelSheets, None


def convertDpiAndMmToPx(length_mm, DPI):
	return round((DPI * length_mm) / 25.4)
