docker build -t report:latest .
for i in `docker images | grep none | awk '{print $3}'`; do docker rmi $i; done
