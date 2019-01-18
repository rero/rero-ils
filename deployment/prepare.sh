#! /bin/sh

# create a namespace
kubectl apply -f ils-namespace.yaml
# create volume claims
# for osx change to storageclass.kubernetes.io/is-default-class: "true"
kubectl apply -f ils-volume-claim-db.yaml --namespace=ils
kubectl apply -f ils-volume-claim-es.yaml --namespace=ils
kubectl apply -f ils-volume-claim-mq.yaml --namespace=ils
kubectl apply -f ils-volume-claim-data.yaml --namespace=ils

# secrets must be set once
# kubectl get secrets ils -o yaml > ils-secrets.yaml
kubectl apply -f ils-secrets.yaml --namespace=ils
# apply the limits
kubectl apply -f ils-limits.yaml --namespace=ils
# apply configmap
kubectl apply -f ils-configmap.yaml --namespace=ils
# apply services
kubectl apply -f ils-services.yaml --namespace=ils


# # kubernets dashboard install with graphs ------------------------------------
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/influxdb.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/grafana.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/heapster.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/rbac/heapster-rbac.yaml
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml
# # get token
# kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep admin-user | awk '{print $1}')

# # start the kubernets dashboard server ---------------------------------------
# kubectl proxy
# http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=ils
