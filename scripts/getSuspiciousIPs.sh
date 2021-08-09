#!/bin/bash
# Copyright 2021 Thomas Lin
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
# 
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
