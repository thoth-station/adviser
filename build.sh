#!/bin/sh

TAG='fridex/thoth-adviser'

docker build . -f Dockerfile -t ${TAG}
docker login -u $DOCKER_USER -p $DOCKER_PASS
docker push ${TAG}
