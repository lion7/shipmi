#!/bin/bash
set -x
DIR=$(readlink -f "${0%%/*}")

#tox
pip install "$DIR"
shipmid --foreground &
PID=$!

shipmi delete test || echo
shipmi add test --port 6023 --provider proxmox-qm

shipmi start test
ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6023 power status || echo
ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6023 power on || echo
ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6023 chassis power on || echo
ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6023 chassis bootdev pxe || echo
shipmi delete test
kill $PID
