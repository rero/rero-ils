#! /bin/sh

VERSION=latest

cd ..
docker system prune -f
pipenv update
docker build  --rm -t rero/rero-ils-nginx:${VERSION} docker/nginx/
docker push rero/rero-ils-nginx:${VERSION}
docker build --rm -t rero/rero-ils-base:${VERSION} -f Dockerfile.base .
docker build --rm -t rero/rero-ils:${VERSION} --build-arg VERSION=${VERSION} -f Dockerfile .
docker push rero/rero-ils:${VERSION}

cd ./deployment

# apply the cache, databse, frontend, indexer, mq, tasksui deployments
kubectl apply -f kubernetes --namespace=ils
# display the created pods
kubectl get pods --namespace=ils

# start setup
kubectl apply -f ils-setup.yaml --namespace=ils
# # display the log for the setup
# kubectl logs -f ils-setup --namespace=ils
# # delete setup
# kubectl delete -f ils-setup.yaml --namespace=ils
