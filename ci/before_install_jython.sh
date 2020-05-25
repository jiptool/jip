#!/bin/sh
set -e

JYTHON_JAR=$(${TRAVIS_BUILD_DIR}/ci/mvnget.sh $JYTHON)
java -jar ${JYTHON_JAR} -s -d $HOME/jython

$HOME/jython/bin/pip install --upgrade pip
$HOME/jython/bin/pip install virtualenv==20.0.10
$HOME/jython/bin/virtualenv $HOME/myvirtualenv
