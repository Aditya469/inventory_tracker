#!/bin/bash

# Copyright 2022 DigitME2
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



# Note that this assumes that the working dir is somewhere under /home/<user>

if (( `id -u`!=0 ))
	then
		echo "Must be run as root. try 'sudo ./installer.sh'"
		exit
fi

echo "This script will install or update the DigitME2 Basic Inventory Tracker"
echo "WARNING: This will make changes to nginx configuration files. Continue? y/n"
read confirmInput
if [[ $confirmInput != "y" ]]; then 
	exit 
fi

INSTALL_DIR=$(awk '{split($0,J,"/"); print "/"J[2]"/"J[3]"" }' <<< `pwd`)
ROOT_DIR=$(awk '{split($0,J,"/"); print "/"J[2]"/"J[3]"/digitme2_inventory_tracker" }' <<< `pwd`)
USER=$(awk '{split($0,J,"/"); print J[3] }' <<< `pwd`)

echo "Server will be installed under $ROOT_DIR"

# set up files with the required root path
sed -i "s|ROOTPATH|$ROOT_DIR|g" inventory_tracker_scheduled_task_worker.service
sed -i "s|ROOTPATH|$ROOT_DIR|g" inventory_tracker_discovery.service
sed -i "s|ROOTPATH|$ROOT_DIR|g" inventory_tracker_server.service
sed -i "s|ROOTPATH|$ROOT_DIR|g" inventory_tracker_interface
sed -i "s|ROOTPATH|$ROOT_DIR|g" digitme2_inventory_tracker/server/paths.py

# Replace the placeholder secret key with a proper value
# Change the secret key to a random string
SECRET_KEY=$(echo $RANDOM | md5sum | head -c 20)
sed -i "s|change_this_key|$SECRET_KEY|g" digitme2_inventory_tracker/server/__init__.py


# set up python venv and install requirements
apt install -y python3.10
apt install -y python3.10-venv
python3.10 -m venv $ROOT_DIR
source $ROOT_DIR/bin/activate
pip install -r requirements.txt


# set up nginx
echo "update and install nginx"
sudo apt update -y
sudo apt -y install nginx
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo rm /etc/nginx/sites-enabled/default

# copy server files to /home/$USER/digitme2_inventory_tracker and set as owned by $USER:www-data
echo "copy files to $INSTALL_DIR"
cp -r digitme2_inventory_tracker $INSTALL_DIR


# copy setup to systemd folder
echo "copy service units to /etc/systemd/system"
cp inventory_tracker_scheduled_task_worker.service /etc/systemd/system
cp inventory_tracker_discovery.service /etc/systemd/system
cp inventory_tracker_server.service  /etc/systemd/system

# copy nginx config files
cp inventory_tracker_interface /etc/nginx/sites-available/inventory_tracker_interface
ln -s /etc/nginx/sites-available/inventory_tracker_interface /etc/nginx/sites-enabled

# move into the server and initialise the DB. Has to be done before anything else starts or it'll cause an error
cd $ROOT_DIR/server
python init_db.py
chown $USER:www-data -R $ROOT_DIR
sudo rm $ROOT_DIR/instance/dbLockFile.lock

# start services and enable at boot
echo "start services"
systemctl daemon-reload
systemctl start inventory_tracker_scheduled_task_worker.service
systemctl enable inventory_tracker_scheduled_task_worker.service

systemctl start inventory_tracker_discovery.service
systemctl enable inventory_tracker_discovery.service

systemctl start inventory_tracker_server.service
systemctl enable inventory_tracker_server.service

systemctl restart nginx

# set up firewall
echo "setup firewall"
ufw allow 'Nginx Full'

echo "setup complete. Open your bowser and go to localhost"
