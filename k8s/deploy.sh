#!/bin/bash

echo Deploy new versions. Argument: $1
date

LOCAL_CLUSTER="minikube"
TEST_CLUSTER="gke_foobar-123456_europe-north1-b_xyzzy-test-cluster"
PROD_CLUSTER="gke_foobar-123456_europe-north1-b_xyzzy-prod-cluster"

SELECTED_CLUSTER=$LOCAL_CLUSTER

if [[ $1 = "prod" ]]
then
    SELECTED_CLUSTER=$PROD_CLUSTER
fi

if [[ $1 = "test" ]]
then
    SELECTED_CLUSTER=$TEST_CLUSTER
fi

echo "Deploy to "$SELECTED_CLUSTER

# 1. Make the Local cluster active
kubectl config set current-context $SELECTED_CLUSTER
# 2. Create/update Cluster
kustomize build overlays/$1/gateway/ | kubectl apply -f -
kustomize build overlays/$1/node-alice/ | kubectl apply -f -

# Starting minikube tunnel so that the loadbalancer service type can work.
if [[ $1 == "local" && $SELECTED_CLUSTER == "minikube" ]]
then
    minikube tunnel &
fi
