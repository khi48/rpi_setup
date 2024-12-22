#!/bin/bash

REAL_USER="kieranhitchcock"
EMAIL=kieranhitchcock28@gmail.com
echo "-----------------------"
echo "Git Setup"
echo "-----------------------"
sudo apt install git
ssh-keygen -t ed25519 -C $EMAIL
cat ~/.ssh/id_ed25519.pub
git config --global user.email $EMAIL
git config --global user.name "khi48"



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

# Updating git commands
cat <<EOT >> /home/kieranhitchcock/.bashrc

# git commands
alias ga="git add ."
alias gc="git commit -m"
alias gp="git push"
EOT

# Updating poetry configs
cat <<EOT >> /home/kieranhitchcock/.bashrc
# poetry export
export PATH="/home/kieranhitchcock/.local/bin:$PATH"
alias p="poetry run python"
#poetry config virtualenvs.in-project true
poetry config keyring.enabled false
EOT

sudo apt install cowsay

sudo apt-get -y install chromium-chromedriver 
sudo raspi-config