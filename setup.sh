#!/bin/bash

REAL_USER="kieranhitchcock"

sudo apt install git

echo "-----------------------"
echo "Docker Setup"
echo "-----------------------"
sudo apt install -y docker
sudo apt install -y docker-compose
sudo groupadd docker
sudo usermod -aG docker ${REAL_USER}
su -s ${REAL_USER}
docker login

curl -sSL https://install.python-poetry.org | python3 -


# Updating bashrc
cat <<EOT >> /home/kieranhitchcock/.bashrc
# poetry export
export PATH="/home/kieranhitchcock/.local/bin:$PATH"
alias p="poetry run python"
#poetry config virtualenvs.in-project true
poetry config keyring.enabled false
EOT

sudo apt install cowsay
