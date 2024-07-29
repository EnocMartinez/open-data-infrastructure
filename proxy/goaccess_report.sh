#!/bin/bash
# config variables

ACCESS_LOG="/opt/odi/proxy/volumes/log/access.log"
REPORT="/opt/odi/proxy/volumes/goaccess/report.html"

# More info at https://goaccess.io/download#docker

echo "Creating GoAccess report"
echo "Parsing Nginx log '${ACCESS_LOG}'"
echo "Output report to '${REPORT}'"

start=$(date +%s)

cat ${ACCESS_LOG} | docker run --rm -i -e LANG=$LANG allinurl/goaccess -a -o html --log-format COMBINED - > ${REPORT}

end=$(date +%s)

echo "done! GoAccess processed logs in $(( end - start)) seconds"
