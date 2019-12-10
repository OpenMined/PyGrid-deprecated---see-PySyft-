
# Instructions

## Running on local minikube setup

* Steps to run things locally
* Minikube
  ```shell
  $ minikube start
  $ eval $(minikube docker-env) (on sh)
  $ eval (minikube docker-env) (on fish)
  ```
* Build Docker images
  ```shell
  $ docker build -t node ./app/websocket/  # Build PyGrid node image
  $ docker build -t gateway ./gateway/  # Build gateway image
  ```

Ref: [Running Local Docker images in Kubernetes](https://dzone.com/articles/running-local-docker-images-in-kubernetes-1)
