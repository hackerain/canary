#!/bin/sh
docker run --name report -v /root/dockerfiles/report/config.yaml:/usr/src/app/config.yaml --rm report $1
