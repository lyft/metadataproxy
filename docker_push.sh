#!/bin/bash
docker login -e $DOCKER_EMAIL -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
export REPO=lyft/metadataproxy
if [ "$TRAVIS_PULL_REQUEST" == "false" ]
then
    export TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
    docker build -f Dockerfile -t $REPO:$COMMIT .
    docker tag $REPO:$COMMIT $REPO:$TAG
    docker push $REPO
fi
