#!/bin/bash
## Run on Batch using AutoUser (root) - will not be able to get the dpkg lock files to install packages otherwise.

apt-get update &&  apt-get upgrade -y

# Optional Line - not needed if user has a graphics card & display installed
apt-get -y install xvfb mesa-utils x11-xserver-utils xdotool gosu
apt-get install zip unzip build-essential -y
# INstall a specific version of Java8:
# apt install openjdk-8-jdk openjdk-8-jre
sudo wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public |  apt-key add -
sudo add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/
apt-get update
apt-get install adoptopenjdk-8-hotspot=8u232-b09-2 -V -y
# Comment out this line after installation:  vim /etc/java-8-openjdk/accessibility.properties
sed -i -e '/^assistive_technologies=/s/^/#/' /etc/java-*-openjdk/accessibility.properties

# Docker
apt install docker.io -y
systemctl start docker
systemctl enable docker
groupadd docker
# echo "$1"
usermod -aG docker $USER

# needed for pyODBC: for unixODBC development headers
apt-get install unixodbc-dev -y
apt-get install python3-dev -y
apt-get install python3-pip -y

echo "setup installation complete"

#Use this command for PAL
# xvfb-run -s '-screen 0 1280x1024x24' ./gradlew runclient


