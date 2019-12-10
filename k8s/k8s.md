
# Instructions

## Running on local minikube setup

* Steps to run things locally
* Build Docker images
  * $ docker build -t node ./app/websocket/  # Build PyGrid node image
  * $ docker build -t gateway ./gateway/  # Build gateway image
* Minikube
  * Minikube start
  * Run eval $(minikube docker-env) (on sh)
  * Run eval $(minikube docker-env) (on fish)

Ref: [Running Local Docker images in Kubernetes](https://dzone.com/articles/running-local-docker-images-in-kubernetes-1)