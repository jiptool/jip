jip
===

Jip is the jython equivalent of pip to python. It will resolve dependencies and 
download jars for your jython environment.

License
-------

jip itself is distributed under the license of GNU General Public License, Version 3.

Install
-------

jip is required to run within virtualenv, which is a best practice for 
python/jython developers to created a standalone, portable environment.

Create virtualenv with jython:

    virtualenv -p /usr/local/bin/jython jython-env

Activate the shell environment:

    cd jython-dev
    source bin/activate

Download and install jip with pip:
    
    pip install jip

Usage
-----

### Install a Java package ###

jip will resolve dependencies and download jars from maven repositories. 
You can install a Java package just like what you do python with pip:

    jip install <groupId>:<artifactId>:<version>

Take spring as example:

    jip install org.springframework:spring-core:3.0.5.RELEASE

### Resolve dependencies defined in a pom ###

jip allows you to define dependencies in a maven pom file, which is more 
maintainable than typing install command one by one:

    jip resolve pom.xml

### Resolve dependencies for an artifact ###
With jip, you can resolve and download all dependencies of an artifact,
without grab the artifact itself (whenever the artifact is downloadable, for example,
just a plain pom). This is especially useful when you are about to setup an environment
for an artifact. Also, java dependencies for a jython package is defined in
this way.

    jip install-dependencies info.sunng.gefr:gefr:0.2-SNAPSHOT

### Update snapshot artifact ###

You can use update command to find and download a new deployed snapshot:

    jip update info.sunng.bason:bason-annotation:0.1-SNAPSHOT

### Run jython with installed java packages in path ###

Another script `jython-all` is shipped with jip. To run jython with Java 
packages included in path, just use `jython-all` instead of `jython`

### Clean ###

`jip clean` will remove everything you downloaded, be careful to use it.

Configuration
-------------

You can configure custom maven repository with a dot file, jip will search
configurations in the following order:

1. `$VIRTUAL_ENV/.jip`, your virtual environment home
1. `$HOME/.jip`, your home

Here is an example:

    [repos:jboss]
    uri=http://repository.jboss.org/maven2/
    type=remote

    [repos:local]
    uri=/home/sun/.m2/repository/
    type=local

    [repos:central]
    uri=http://repo1.maven.org/maven2/
    type=remote

Be careful that the .jip file will overwrite default settings, 
so you must include default local and central repository explicitly. 
jip will skip repositories once it finds package matches the maven coordinator.


Links
-----

* [http://sunng.info/blog/jip-0-1](http://sunng.info/blog/jip-0-1/ "a more comprehensive guide")
* [http://pypi.python.org/pypi/jip](http://pypi.python.org/pypi/jip "Python cheese shop")


