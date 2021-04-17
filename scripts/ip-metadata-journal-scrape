#!/usr/bin/python3
import select
import sys
import re
import requests

from systemd import journal

IPMETA_SERV_API = "http://localhost:4040/api/%s"

sshJourn = journal.Reader()
sshJourn.add_match(_SYSTEMD_UNIT="ssh.service")
#sshJourn.log_level(journal.LOG_INFO)
sshJourn.seek_tail()

# Need to call get_previous() after seek_tail()
#   See: https://bugs.freedesktop.org/show_bug.cgi?id=64614
# TODO: See if latest systemd is fixed
# NOTE: get_previous() acts as a seek back 1 and then get_next()
sshJourn.get_previous()

p = select.poll()
p.register(sshJourn, sshJourn.get_events())
while p.poll():
    if sshJourn.process() != journal.APPEND:
        continue

    for entry in sshJourn:
        msg = entry.get('MESSAGE')
        date = entry.get('_SOURCE_REALTIME_TIMESTAMP')
        if not msg or ("Invalid user" not in msg and "Failed password" not in msg):
            continue

        # Parse IP
        res = re.search('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', msg)
        if not res:
            continue

        # Make call to IP metadata server
        ip = res.group()
        res = requests.get(IPMETA_SERV_API % ip)

        if res.status_code != 200:
            print("ERROR: IP metadata server returned %s %s" % (res.status_code, res.reason))
            continue

        print("\n==========")
        print("%s %s: %s" % (date, ip, res.json()))

