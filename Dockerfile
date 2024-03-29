# NOTE you cannot use inline comments-- do not put a comment at end of line, you'll get a very obscure error.

FROM ubuntu:18.04

RUN apt-get update && apt-get -y install openjdk-8-jdk xvfb mesa-utils x11-xserver-utils xdotool gosu sudo acl curl zip unzip build-essential && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
ADD . /PAL

RUN cd /PAL && ./gradlew --continue --project-cache-dir /tmp/gradle-cache -g /tmp/client-home runclient || true
#RUN sudo chmod -R a+rwx /root
#RUN sudo chmod -R a+rwx /PAL
#RUN ls
#RUN ./gradlew build
#CMD ["/bin/bash"]