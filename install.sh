#!/bin/bash

set -x

INSTALL_DIR=/opt/gardensmart

SYSTEMD_DIR=/etc/systemd/system/

mkdir -p $INSTALL_DIR/etc

mkdir -p $INSTALL_DIR/certs
mkdir -p $INSTALL_DIR/db
mkdir -p $INSTALL_DIR/log

cp -f *.py $INSTALL_DIR/
cp -f *.service $INSTALL_DIR/
cp -uf etc/*.json $INSTALL_DIR/etc

ln -sf $INSTALL_DIR/gs_irrigator.service $SYSTEMD_DIR/gs_irrigator.service


