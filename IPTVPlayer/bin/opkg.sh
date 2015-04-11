#!/bin/bash
#
# author j00zek 2014
#
#

install_package(){
opkg install $1 1>/dev/null 2>&1
if [ $? -eq 0 ]; then
	echo "$1 installed correctly"
	echo "$1 installed correctly">/tmp/IPTV-opkg.log
fi
}

install_package python-compression
install_package python-json
install_package python-simplejson
install_package python-html
install_package python-image
install_package python-imaging
install_package python-mechanize
install_package python-mutagen
install_package python-robotparser
install_package python-shell
install_package gst-plugins-bad-rtmp
install_package librtmp0
install_package gst-plugins-good
install_package gst-plugins-bad-cdxaparse
install_package gst-plugins-bad-vcdsrc 
exit 0