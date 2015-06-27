# Setting up Buildbot Slaves #

Setting up a buildbot slave is pretty easy. There's only a few things that need to be installed.

Right now we only support buildbot on Linux systems, but in the future we'll work toward Windows as well. This document also assumes Debian or Ubuntu in some places. You may have to make adjustments for other Linux distributions.


## Choosing the right Python version ##

These instructions are assuming that the default version of Python on the system is the version you want to use for testing. If using a separate version, you'll need to install the support and use the appropriate commands. For example:

```
$ sudo apt-get install python2.4 python2.4-dev python2.4-setuptools
```

Then use `easy_install-2.4` below.

On Ubuntu 9.04 and higher, Python 2.4 is deprecated, and support isn't automatically available for setuptools. For this, download the egg and install it manually using the [setuptools installation instructions](http://pypi.python.org/pypi/setuptools).


## Dependencies ##

First, you'll need some packages used in the testing. These are best installed through your distribution's native package:

```
$ sudo apt-get install subversion libsvn-dev python-setuptools pyflakes git-core mercurial
```

You'll then need to get some Python-specific modules on your system:

```
$ sudo easy_install virtualenv P4PythonInstaller
```

The buildbot steps will install PIL (Python Imaging Library) and PySVN, which will have to compile a few things. You'll need gcc and the Python development headers for this, as well as some other development packages. On Debian/Ubuntu, this is easily done:

```
$ sudo apt-get build-dep python-imaging python-svn
```

Finally, buildbot itself:

```
$ sudo apt-get install buildbot
```

If your version of buildbot is earlier than 0.7.10, then run the following (using the default `easy_install` version), after the install above:

```
$ sudo easy_install -U buildbot
```

It's important to install the system package first in order to get the init scripts.


## Creating the Slave ##

Slaves generally live in `/var/lib/buildbot` somewhere. To keep it organized, I recommend something like `/var/lib/buildbot/slaves/reviewboard`. Assuming this setup, do the following:

```
$ sudo mkdir -p /var/lib/buildbot/slaves/reviewboard
$ sudo buildbot create-slave /var/lib/buildbot/slaves/reviewboard build.review-board.org:9989 _slavename_ _password_
```


The slave name and password are pretty much up to you. I recommend including the distro name and version, and the Python version. We'll need both the name and password to finish setup on our end.


Once this is complete, go into the new slave directory and type:

```
$ sudo ln -s `which virtualenv` virtualenv
```


Then we'll want to make sure we have the scripts necessary for the slave. In the new slave directory, run:

```
$ sudo git init
$ sudo git remote add origin git://github.com/reviewboard/rb-buildbot-slave-config.git
$ sudo git pull origin master
```

Change the ownership of the buildbot directory and its contents.

```
$ sudo chown -R buildbot:nogroup /var/lib/buildbot
```

Now register this buildbot so that it will start up along with the system. Add the following to `/etc/default/buildbot`:

```
BB_NUMBER[0]=0
BB_NAME[0]="Review Board slave"
BB_USER[0]="buildbot"
BB_BASEDIR[0]="/var/lib/buildbot/slaves/reviewboard"
BB_OPTIONS[0]=""
BB_PREFIXCMD[0]=""
```


This should be all that's needed!