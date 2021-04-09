#!/bin/bash
if [[ $# -ne 1 ]]; then
    echo "ERROR: Specify the number of previous days of logs to search through"
    exit 1
else
    NUM_DAYS=$1
fi

if [[ ${NUM_DAYS} -gt 0 ]]; then
    IPs=`journalctl --since "${NUM_DAYS} days ago" -u ssh.service |  grep -E "(Invalid user|Failed password)" | grep -E -o "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | sort | uniq`

    for IP in ${IPs}; do
        echo "Querying for: " ${IP}
        curl localhost:4040/api/${IP}
        echo
    done
fi
