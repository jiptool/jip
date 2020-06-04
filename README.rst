jip
===

.. image:: https://img.shields.io/travis/jiptool/jip/master.svg
   :target: https://travis-ci.org/jiptool/jip
.. image:: https://img.shields.io/pypi/v/jip.svg?maxAge=2592000   :target: https://pypi.python.org/pypi/jip
.. image:: https://img.shields.io/pypi/l/jip.svg?maxAge=2592000   :target:


Jip is the jython equivalent of pip to python. It will resolve
dependencies and download jars for your jython environment.

License
-------

jip itself is distributed according to **MIT License** .

Install
-------

jip is recommended to run within virtualenv, which is a best practice
for python/jython developers to created a standalone, portable
environment. From jip 0.7, you can use jip.embed in the global installation.

Install jip within virtualenv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create virtualenv with jython:

::

    virtualenv -p /usr/local/bin/jython jython-env

Activate the shell environment:

::

    cd jython-dev
    source bin/activate

Download and install jip with pip:

::

    pip install jip

Install jip for global jython (since 0.7)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download jip from `pypi page <http://pypi.python.org/pypi/jip>`_ .
Then install it with setup.py

::

    jython setup.py install

Usage
-----

Install a Java package
~~~~~~~~~~~~~~~~~~~~~~

jip will resolve dependencies and download jars from maven
repositories. You can install a Java package just like what you do
python with pip:

::

    jip install <groupId>:<artifactId>:<version>

Take spring as example:

::

    jip install org.springframework:spring-core:3.0.5.RELEASE

Resolve dependencies defined in a pom
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

jip allows you to define dependencies in a maven pom file, which is
more maintainable than typing install command one by one:

::

    jip resolve pom.xml

Resolve dependencies for an artifact
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With jip, you can resolve and download all dependencies of an
artifact, without grab the artifact itself (whenever the artifact
is downloadable, for example, just a plain pom). This is especially
useful when you are about to setup an environment for an artifact.
Also, java dependencies for a jython package is defined in this
way.

::

    jip deps info.sunng.gefr:gefr:0.2-SNAPSHOT

Update snapshot artifact
~~~~~~~~~~~~~~~~~~~~~~~~

You can use update command to find and download a new deployed
snapshot:

::

    jip update info.sunng.bason:bason-annotation:0.1-SNAPSHOT

Run jython with installed java packages in path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Another script ``jython-all`` is shipped with jip. To run jython
with Java packages included in path, just use ``jython-all``
instead of ``jython``

List
~~~~

Use ``jip list`` to see artifacts you just installed

Remove a package
~~~~~~~~~~~~~~~~

You are suggested to use ``jip remove`` to remove an artifact. This
will keep library index consistent with file system.

::

    jip remove org.springframework:spring-core:3.0.5.RELEASE

Currently, there is no dependency check in artifact removal. So you should
be careful when use this command.

Clean
~~~~~

``jip clean`` will remove everything you downloaded, be careful to
use it.

Search
~~~~~~

You can also search maven central repository with a ``jip search [keyword]``.
The search service is provided by
`Sonatype's official Maven search <http://search.maven.org>`_ .

Persist current environment state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you distribute you environment, you can use ``freeze`` to persist
current state into a pom file.

::

    jip freeze > pom.xml


Configuration
-------------

You can configure custom maven repository with a dot file, jip will
search configurations in the following order:


1. ``$VIRTUAL_ENV/.jip_config``, your virtual environment home
2. ``$HOME/.jip_config``, your home

Here is an example:

::

    [repos:jboss]
    uri=http://repository.jboss.org/maven2/
    type=remote

    [repos:local]
    uri=~/.m2/repository/
    type=local

    [repos:central]
    uri=https://repo1.maven.org/maven2/
    type=remote

Be careful that the ``.jip_config`` file will overwrite default settings,
so you must include default local and central repository explicitly.
jip will skip repositories once it finds package matches the maven
coordinator.

Artifacts will be cached at ``$HOME/.jip`` (``$VIRTUAL_ENV/.jip`` if
you are using a virtual environment).

From 0.4, you can also define repositories in pom.xml if you use
the ``resolve`` command. jip will add these custom repositories
with highest priority.

Distribution helpers
--------------------

From 0.4, you can use jip in your setup.py to simplify jython
source package distribution. Create ``pom.xml`` in the same directory
with setup.py. Fill it with your Java dependencies in standard way.
In this file, you can also define custom repositories. Here is
an example:

::

    <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">

        ...

        <dependencies>
            <dependency>
                <groupId>org.slf4j</groupId>
                <artifactId>slf4j-api</artifactId>
                <version>1.6.1</version>
            </dependency>

            <dependency>
                <groupId>org.slf4j</groupId>
                <artifactId>slf4j-log4j12</artifactId>
                <version>1.6.1</version>
            </dependency>

            ...

        </dependencies>

        <repositories>
            <repository>
                <id>sonatype-oss-sonatype</id>
                <url>http://oss.sonatype.org/content/repositories/snapshots/</url>
            </repository>
        </repositories>
    </project>

And in your setup.py, use the jip setup wrapper instead of the one
provided by setuptools or distutils. You can add keyword argument
``pom`` to specify a custom name of the pom file.

::

    from jip.dist import setup

Other than the traditional pom configuration, jip also allows you to
describe dependencies in python. You can define a data structure in
your ``setup.py`` like:

::

    requires_java = {
        'dependencies':[
            ## (groupdId, artifactId, version)
            ('org.slf4j', 'slf4j-api', '1.6.1'),
            ('org.slf4j', 'slf4j-log4j12', '1.6.1'),
            ('info.sunng.soldat', 'soldat', '1.0-SNAPSHOT'),
            ('org.apache.mina', 'mina-core', '2.0.2')
        ],
        'repositories':[
            ('sonatype-oss-snapshot', 'http://oss.sonatype.org/content/repositories/snapshots/')
        ]
    }

And pass it to jip setup as keyword argument ``requires_java``. Once
jip found this argument, it won't try to load a pom file.

::

    from jip.dist import setup
    setup(
        ...
        requires_java=requires_java,
        ...)

Another ``resolve`` command was added to setuptools, you can use this
command to download all dependencies to library path

::

    jython setup.py resolve

All dependencies will be installed when running

::

    jython setup.py install

So with jip's ``setup()`` wrapper, ``pip`` will automatically install
what your package needs. You can publish your package to python
cheese shop, and there is just one command for everything

::

    pip install [your-package-name]


Embedded dependency helper
--------------------------

jip.embed is available for both virtualenv and global installation.
You can descirbe Java dependency in you code, then it will be
resolved on the fly.
jip.embed is inspired by Groovy's @Grab.

::

    from jip.embed import require

    require('commons-lang:commons-lang:2.6')
    from org.apache.commons.lang import StringUtils

    StringUtils.reverse('jip rocks')

Contact
-------

If you have any problem using jip, or feature request for jip,
please feel free to fire an issue on
`github issue tracker <http://github.com/jiptool/jip/issues/>`_. You can
also follow `@Sunng <http://twitter.com/Sunng/>`_ on twitter.

Change Notes
------------

- Next version - unreleased
- 0.9.15 - 2020-06-04

  - Fix encoding errors of download from local repositories

- 0.9.14 - 2020-05-25

  - Added Python 3.7 compatibility
  - Fail gracefully if unkown repository type
  - Maven central `moved to HTTPS <https://blog.sonatype.com/central-repository-moving-to-https>`_

- 0.9.13 - 2017-07-23

  - Added option `copy-pom` for `install` command

- 0.9.12 - 2017-03-20

  - Fix errors when downloading POMs containing umlauts
  - Remove jip.JIP_VERSION. Use jip.__version__ if you need it

- 0.9.11 - 2017-03-11

  - Improve handling of download errors

- 0.9.10 - 2017-03-09

  - Fix .jip/cache not being isolated in virtualenv

- 0.9.9 - 2016-10-31

  - Fix possible crash

- 0.9.8 - 2016-07-27

  - Minor fixes

- 0.9 - 2015-04-23

  - Python 3 support

- 0.8 - 2014-03-31

  - Windows support

- 0.7 - 2011-06-11

  - All new jip.embed and global installation
  - enhanced search
  - dry-run option for ``install``, ``deps`` and ``resolve``
  - exclusion for ``install`` command and jip.dist
  - local maven repository is disabled by default
  - improved dependency resolving speed
  - jip now maintains a local cache of jars and poms in
    ``$HOME/.jip/cache/``
  - use argparse for better command-line ui
  - add some test cases

- 0.5.1 - 2011-05-14

  - Artifact jar package download in paralell
  - User-agent header included in http request
  - new command `freeze` to dump current state
  - bugfix

- 0.4 - 2011-04-15

  - New commands available: ``search``, ``deps``, ``list``, ``remove``
  - New feature ``jip.dist`` for setuptools integration
  - Dependency exclusion support, thanks *vvangelovski*
  - Allow project-scoped repository defined in ``pom.xml`` and
    ``setup.py``
  - Code refactoring, now programming friendly
  - README converted to reStructuredText
  - Migrate to MIT License

- 0.2.1 - 2011-04-07

  - Improved console output format
  - Correct scope dependency management inheritance
  - Alpha release of snapshot management, you can update a snapshot
    artifact
  - Environment independent configuration. ``.jip`` for each
    environment
  - Bug fixes

- 0.1 - 2011-01-04

  - Initial release

Links
-----

-  `Don't repeat yourself: Distribute jython packages with jip.dist <http://sunng.info/blog/2011/04/dont-repeat-yourself-distribute-jython-package-with-jip-dist/>`_
-  **Obsolete**
   `Introduction to jip 0.1 <http://sunng.info/blog/jip-0-1/>`_
-  `Project on Github <http://github.com/sunng87/jip>`_
-  `Package on Python Cheese Shop <http://pypi.python.org/pypi/jip>`_
