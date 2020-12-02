#!/bin/bash
## Run on Batch using AutoUser (root) - will not be able to get the dpkg lock files to install packages otherwise.
## Disable auto-updates that can force a node to reboot and requeue tasks
sudo systemctl disable --now apt-daily.timer
sudo systemctl disable --now apt-daily-upgrade.timer
sudo systemctl daemon-reload

while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get update &&  apt-get upgrade -y
#  apt-get install lubuntu-desktop -y
#  apt-get install xrdp -y
#  systemctl start xrdp
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get install zip unzip build-essential -y
# INstall a specific version of Java8:
# apt install openjdk-8-jdk openjdk-8-jre
sudo wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public |  apt-key add -
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; sudo add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get update
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get install adoptopenjdk-8-hotspot=8u232-b09-2 -V -y
# Comment out this line after installation:  vim /etc/java-8-openjdk/accessibility.properties
sed -i -e '/^assistive_technologies=/s/^/#/' /etc/java-*-openjdk/accessibility.properties

# Docker
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt install docker.io -y
systemctl start docker
systemctl enable docker
groupadd docker
# echo "$1"
usermod -aG docker $USER

whoami
# exec sudo su -l "$1"

sudo su -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -"
#Ubuntu 18.04
sudo su -c "curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list > /etc/apt/sources.list.d/mssql-release.list"

while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get update
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; ACCEPT_EULA=Y apt-get install msodbcsql17 -y
# optional: for bcp and sqlcmd
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; ACCEPT_EULA=Y apt-get install mssql-tools -y
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
# optional: for unixODBC development headers
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get install unixodbc-dev -y
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get install python3-dev -y
while sudo fuser /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do echo "Waiting for release of apt locks"; sleep 2; done; apt-get install python3-pip -y


## Ignore Python 3.8 for now.
rm /usr/bin/python
ln -s /usr/bin/python3.6 /usr/bin/python
echo "setup installation complete"

#Use this command for PAL
# xvfb-run -s '-screen 0 1280x1024x24' ./gradlew runclient


