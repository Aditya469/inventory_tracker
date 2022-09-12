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

import email.message
import email.utils
import logging
import smtplib
import ssl
import threading
from db import getDbSession


# the sending part of this runs on a different thread to prevent the system hanging
from dbSchema import Settings


def sendEmail(receiverAddressList, subject, emailBody):

    dbSession = getDbSession()
    settings = dbSession.query(Settings).first()
    if settings.sendEmails is not True:
        logging.info("Skip sending email due to settings configuration")
        return

    context = ssl.create_default_context()

    msg = email.message.Message()
    msg['From'] = settings.emailAccountName
    msg['To'] = ", ".join(receiverAddressList)
    msg['Subject'] = subject
    msg.add_header('Content-Type', 'text')
    msg.set_payload(emailBody)

    if settings.emailSecurityMethod == "SSL":
        def sendEmailSSL(serverName, serverPort, context, accountName, accountPassword, msg):
            with smtplib.SMTP_SSL(serverName, serverPort, context=context) as server:
                server.login(accountName, accountPassword)
                server.sendmail(msg['From'], msg['To'], msg.as_string())

        threading.Thread(
            target=sendEmailSSL,
            args=(
                settings.emailSmtpServerName,
                settings.emailSmtpServerPort,
                context,
                settings.emailAccountName,
                settings.emailAccountPassword,
                msg
            )
        ).start()

    elif settings.emailSecurityMethod == 'TLS':
        def sendEmailTLS(serverName, serverPort, context, accountName, accountPassword, msg):
            with smtplib.SMTP(serverName, serverPort) as server:
                server.starttls(context=context)
                server.login(accountName, accountPassword)
                server.sendmail(msg['From'], msg['To'], msg.as_string())

        threading.Thread(
            target=sendEmailTLS,
            args=(
                settings.emailSmtpServerName,
                settings.emailSmtpServerPort,
                context,
                settings.emailAccountName,
                settings.emailAccountPassword,
                msg
            )
        ).start()
