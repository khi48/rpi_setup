#!/bin/bash

sudo apt install git

echo "-----------------------"
echo "Docker Setup"
echo "-----------------------"
sudo apt install -y docker
sudo apt install -y docker-compose
sudo groupadd docker
sudo usermod -aG docker ${USER}
su -s ${USER}
docker login

curl -sSL https://install.python-poetry.org | python3 -

sudo apt install cowsay
