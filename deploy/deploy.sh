#!/bin/bash

# Simple Web Server for testing the deployment
sudo apt update -y
sudo apt install apache2 -y
sudo systemctl start apache2
echo """
<h1 style='color:#f09764; text-align:center'>
    OpenMined First Server Deployed via Terraform
</h1>
""" | sudo tee /var/www/html/index.html

## Docker & Docker-Compose installation

sudo apt-get remove docker docker-engine docker.io containerd runc # Uninstall old versions
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose


### Clonning PyGrid

git clone https://github.com/OpenMined/PyGrid
cd PyGrid
sudo echo """
127.0.0.1 network
127.0.0.1 bob
127.0.0.1 alice
127.0.0.1 bill
127.0.0.1 james
""" >> /etc/hosts

sudo docker-compose up
