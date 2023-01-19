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

# File containing email message functions that may be sent out as notifications.
# All in one place for convenience.

from db import getDbSession
from dbSchema import ProductType


def getUserCreatedMessage(username, initialPassword):
    message = f"Hi {username}, \n\n" \
        f"An account has been created for you on the DigitME2 Inventory Tracking system.\n\n" \
        f"Your username is {username} and your password is {initialPassword}.\n"\
        f"Please log in and change this password.\n\n"\
        f"This is an automated email. This inbox is not monitored"

    return message


def getPasswordResetMessage(username, newPassword):
    message = f"Hi {username}, \n\n" \
        f"Your password on the DigitME2 Inventory Tracking system has been reset.\n\n" \
        f"Your new password is {newPassword}.\n"\
        f"Please log in and change this password.\n\n"\
        f"This is an automated email. This inbox is not monitored"

    return message


def getStockCheckInformationMessage(ProductsNeedingReorder, ExpiringStock, ExpiredStock):
    dbSession = getDbSession()

    message = "Hi.\n\nThis is an automated message with the results of a stock check.\n\n"

    if len(ProductsNeedingReorder) > 0:
        message += "The following items are below specified minimum levels and should be reordered\n\n"

        for product in ProductsNeedingReorder:
            message += f"{product.productName}\n"
    else:
        message += "No product types need reordering."

    if len(ExpiringStock) > 0:
        message += "\n\nThe following items are close to their expiry dates:\n"

        message += "\n{:<15} {:<30} {:<20}".format("Item ID", "Product Type", "Expiry Date")
        for stockItem in ExpiringStock:
            message += f"\n{stockItem.idString:<15} {stockItem.associatedProduct.productName:<30} {stockItem.expiryDate.strftime('%d/%m/%Y')}"
    else:
        message += "\n\nNo stock items are close to expiring"

    if len(ExpiredStock) > 0:
        message += "\n\nThe following items have expired:\n"

        message += "\n{:<15} {:<30} {:<20}".format("Item ID", "Product Type", "Expiry Date")
        for stockItem in ExpiredStock:
            message += f"\n{stockItem.idString:<15} {stockItem.associatedProduct.productName:<30} {stockItem.expiryDate.strftime('%d/%m/%Y')}"
    else:
        message += "\n\nNo stock items have expired"

    message += f"\n\nThis is an automated email. This inbox is not monitored"

    return message


def getDatabaseBackupSuccessNotificationMessage(newDatabaseBackupName):
    message = f"Hi, \n\n" \
        f"This is a notification regarding the database backup of the inventory tracking system.\n\n" \
        f"The database has been backed up successfully. The new backup name is:\n\n\t{newDatabaseBackupName}\n\n" \
        f"This is an automated email. This inbox is not monitored"

    return message


def getDatabaseBackupFailureNotificationMessage(error):
    message = f"ATTENTION REQUIRED, \n\n" \
        f"This is a notification regarding the database backup of the inventory tracking system.\n\n" \
        f"The backup of the database failed.\n"

    if error:
        message += f"The error message is {error}\n"

    f"\nThis is an automated email. This inbox is not monitored"

    return message


def getTestEmailMessage():
    message = "This is a test email from the DigitME2 Inventory Tracking system.\n\n" \
              "If you're reading this, it worked!\n\n" \
              "This is an automated email. This inbox is not monitored"

    return message
