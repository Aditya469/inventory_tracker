# DigitME2 Basic Inventory Tracker Server

This directory contains the software for the inventory tracker server.

The server is a Flask WSGI server, intended to run through Nginx and Gunicorn. There is also a small script (schedueTaskWorker.py) that should run periodically to execute backup and stock processing tasks.
