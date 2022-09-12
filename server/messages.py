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


def getStockNeedsReorderingMessage(productIdList):
    dbSession = getDbSession()
    productList = dbSession.query(ProductType)\
        .filter(ProductType.id.in_(productIdList))\
        .order_by(ProductType.productName.asc())\
        .all()

    message = "Hi.\n\nThis is an automated message regarding stock levels. " \
              "The following items are below specified minimum levels:\n\n"

    for product in productList:
        message += f"{product.productName}\n"

    message += f"\nThis is an automated email. This inbox is not monitored"

    return message
