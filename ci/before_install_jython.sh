#!/bin/sh
set -e

JYTHON_JAR=$(${TRAVIS_BUILD_DIR}/ci/mvnget.sh $JYTHON)
java -jar ${JYTHON_JAR} -s -d $HOME/jython

$HOME/jython/bin/pip install --upgrade pip
$HOME/jython/bin/pip install 
$HOME/jython/bin/virtualenv $HOME/myvirtualenvvirtualenv=16.5.0
