#!/bin/sh
pip3 install -r ${SRC_PKG}/src/requirements.txt -t ${SRC_PKG}/src -i https://pypi.tuna.tsinghua.edu.cn/simple/
cp -r ${SRC_PKG}/src ${DEPLOY_PKG}