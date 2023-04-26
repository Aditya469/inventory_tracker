# DigitME2 Basic Inventory Tracker

This system offers an introductory Inventory Tracking solution, intended for small businesses.

The system comprises a server, which runs on an Ubuntu Linux 22.04 computer on premise, and an Android app. The server provides a convenient browser interface, which allows the system to be administered. This supports multiple users, and allows different login levels for different users for the purpose of access control. The app is used to add items of stock to the system and to check items in and out of storage.

Stock may be assigned to jobs, and the system provides an ability to track the runnning total cost of jobs.

Items are tracked using the android app and simple QR code labels. These are intended to be printed onto sticker sheets, and the individual stickers then attached to items, thereby providing a cheap and effective means of identifying them.

The system is also capable of performing an automatic stock check and reporting the results. These results include alerts for stock that needs reordering, and stock which has expired or is about to expire. Results are delivered as an email notification. The server will require an email account to be set up for it to use. We recommend Outlook for this.

The app can tolerate an intermittent connection to the server, and so will continue to function even if your storage area is out of range of the Wi-Fi. Please note that since the app syncs to the server periodically, this system only supports a single instance of the app running at once. We recommend that one person be assigned to all movement of stock in and out of storage.
