#!/bin/bash
# Note that this assumes that the working dir is somewhere under /home/<user>

if (( `id -u`!=0 ))
	then
		echo "Must be run as root"
		echo "USAGE: sudo ./installer.sh"
		exit
fi
echo "begin setup"

INSTALL_DIR=$(awk '{split($0,J,"/"); print "/"J[2]"/"J[3]"" }' <<< `pwd`)
ROOT_DIR=$(awk '{split($0,J,"/"); print "/"J[2]"/"J[3]"/digitme2_inventory_tracker" }' <<< `pwd`)
USER=$(awk '{split($0,J,"/"); print J[3] }' <<< `pwd`)

echo "Server will be installed under $ROOT_DIR"

# set up files with the required root path
cp inventory_tracker_scheduled_task_worker.service tmp.txt
sed "s|ROOTPATH|$ROOT_DIR|g" tmp.txt > inventory_tracker_scheduled_task_worker.service

cp inventory_tracker_discovery.service tmp.txt
sed "s|ROOTPATH|$ROOT_DIR|g" tmp.txt > inventory_tracker_discovery.service

cp inventory_tracker_server.service tmp.txt
sed "s|ROOTPATH|$ROOT_DIR|g" tmp.txt > inventory_tracker_server.service

cp inventory_tracker_interface tmp.txt
sed "s|ROOTPATH|$ROOT_DIR|g" tmp.txt > inventory_tracker_interface

cp digitme2_inventory_tracker/server/paths.py tmp.txt
sed "s|ROOTPATH|$ROOT_DIR|g" tmp.txt > digitme2_inventory_tracker/server/paths.py

rm tmp.txt

# set up python venv and install requirements
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y
aup update
apt install -y python3.8-venv
python3.8 -m venv $ROOT_DIR
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
