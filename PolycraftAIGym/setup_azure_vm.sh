#!/bin/bash
## Run using SUDO
apt-get update &&  apt-get upgrade -y
#  apt-get install lubuntu-desktop -y
#  apt-get install xrdp -y
#  systemctl start xrdp
apt-get -y install xvfb mesa-utils x11-xserver-utils xdotool gosu
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

whoami
# exec sudo su -l "$1"

sudo su -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -"
#Ubuntu 18.04
sudo su -c "curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list > /etc/apt/sources.list.d/mssql-release.list"

apt-get update
ACCEPT_EULA=Y apt-get install msodbcsql17 -y
# optional: for bcp and sqlcmd
ACCEPT_EULA=Y apt-get install mssql-tools -y
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
# optional: for unixODBC development headers
apt-get install unixodbc-dev -y
apt-get install python3-dev -y 
apt-get install python3-pip -y


mkdir polycraft && cd polycraft 
# # TODO: update to the correct branch:
git clone -b dev_unix_sri --single-branch https://github.com/StephenGss/pal.git
cd pal/

# TODO: Move private_tests/ from the zip file to the right place inside the pal folder.
# mv where/is/private_tests/ ~/polycraft/pal/
# chmod +x private_tests/sri_dryrun_mock/build.sh
#  apt-get install python3.8 
# Ignore Python 3.8 for now.
rm /usr/bin/python
ln -s /usr/bin/python3.6 /usr/bin/python
python -m pip install -U pip 
python -m pip install -r requirements.txt

# chown -R $HOME/polycraft/ azureuser:azureuser

echo "setup installation complete"

#Use this command for PAL
# xvfb-run -s '-screen 0 1280x1024x24' ./gradlew runclient


