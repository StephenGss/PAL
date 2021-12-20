#!/bin/bash
## Run on Batch using AutoUser (root) - will not be able to get the dpkg lock files to install packages otherwise.

apt-get update &&  apt-get upgrade -y

# Optional Line - not needed if user has a graphics card & display installed
apt-get -y install xvfb mesa-utils x11-xserver-utils xdotool gosu
apt-get install zip unzip build-essential -y
# apt install openjdk-8-jdk openjdk-8-jre
apt-get install openjdk-8-jdk-headless -V -y

# needed for pyODBC: for unixODBC development headers
apt-get install unixodbc-dev -y
apt-get install python3-dev -y
apt-get install python3-pip -y

echo "setup installation complete"

#Use this command for PAL
# xvfb-run -s '-screen 0 1280x1024x24' ./gradlew runclient