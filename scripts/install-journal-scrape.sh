#!/bin/bash
if [[ $# -ne 1 ]]; then
    echo "ERROR: Expecting only one argument (IP metadata server base URL, e.g. http://localhost:4040)"
    exit 1
else
    IPMETA_BASE_URL=$1
fi


SCRIPT_DIR=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
LOCAL_BIN_PATH=/usr/local/bin

# Create systemd service file if it doesn't exist
SERV_NAME=ip-metadata-journal-scrape
SYSTEMD_SERVICE=/lib/systemd/system/${SERV_NAME}.service
if [[ -f ${SYSTEMD_SERVICE} ]]; then
    # Previous installation may exist, stop it first
    echo "Stopping service..."
    sudo service ${SERV_NAME} stop
fi

# Always replace systemd service file (in case user changes URL of IP metadata service)
TMP_SERVICE=`mktemp`
cat <<TLINEND >> ${TMP_SERVICE}
[Unit]
Description=IP Metadata Journal Scraper
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
TimeoutStopSec=30
ExecStart=${LOCAL_BIN_PATH}/${SERV_NAME} ${IPMETA_BASE_URL}
ExecStop=/bin/kill -TERM \$MAINPID

[Install]
WantedBy=multi-user.target
TLINEND

# Move to final location
sudo mv ${TMP_SERVICE} ${SYSTEMD_SERVICE} && sudo chmod og+r ${SYSTEMD_SERVICE}

# Move/replace script
sudo cp -a ${SCRIPT_DIR}/${SERV_NAME} ${LOCAL_BIN_PATH}

# Enable via systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable ${SERV_NAME}

echo "Starting service..."
sudo service ${SERV_NAME} start

