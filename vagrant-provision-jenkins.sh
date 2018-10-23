#!/usr/bin/env bash

apt-get update -y
apt-get install -y wget curl git make zip unzip
apt-get upgrade -y

# Java
echo deb http://ftp.debian.org/debian jessie-backports main > /etc/apt/sources.list.d/backports.list
apt-get update -y
apt-get install -y \
    -t jessie-backports \
    openjdk-8-jre-headless \
    ca-certificates-java

# Jenkins
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list
apt-get update -y
apt-get install -y jenkins

# Docker
apt-get install -y \
     apt-transport-https \
     ca-certificates \
     gnupg2 \
     software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
apt-get update -y
apt-get install -y docker-ce

# Jenkins -> Docker
sudo usermod -a -G docker jenkins
echo "Reboot for docker permissions to take effect"
