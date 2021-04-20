IMAGE=pal
#BUILD_AFTER_IMAGE = (cd ../../test; ../prt/prt polycraft-build.prt)
include ../common/Makefile-header
include ../common/Makefile-body

#cd polycraftOG/
#export JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF8
#Xvfb :55 -screen 0 800x600x24 &
#export DISPLAY=:55
#echo $DISPLAY
#./gradlew setupDecompWorkspace
#./gradlew build
#./gradlew runClient
