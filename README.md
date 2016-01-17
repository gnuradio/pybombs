# PyBOMBS

Website: http://gnuradio.org/pybombs

Minimum Python version: 2.7

## License

Copyright 2015 Free Software Foundation, Inc.

This file is part of PyBOMBS

PyBOMBS is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3, or (at your option)
any later version.

PyBOMBS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PyBOMBS; see the file COPYING.  If not, write to
the Free Software Foundation, Inc., 51 Franklin Street,
Boston, MA 02110-1301, USA.

## Installation

PyBOMBS can be installed using Python's setuptools. From the top
level of the source code repository, run

    $ python setup.py build

or

    $ sudo python setup.py install

This will install PyBOMBS and all required dependencies. See

    $ python setup.py build --help
    $ python setup.py install --help

for additional settings.

For development purposes, it's possible to run PyBOMBS without
installation. Simply run `pybombs/main.py` and make sure `pybombs/`
is in reach. pip also provides a `-e` switch for installing PyBOMBS
in 'editable' mode.

## Quickstart

For the impatient:

1. Install PyBOMBS as per the previous section
2. Add a list of recipes, e.g. by running

    $ pybombs recipes add gnuradio git+https://github.com/gnuradio/recipes2.git
    $ # Note: This URL will likely change soon.

3. Create a prefix (a place to store your local installation):

    $ pybombs prefix init /path/to/prefix -a myprefix

4. Start installing:

    $ pybombs -p myprefix install gnuradio gr-osmosdr

5. Optional: Make your prefix the default (this will save you having to type `-p myprefix`):

    $ pybombs config default_prefix myprefix

## Prefixes

A prefix is a directory into which packages are installed.
The prefix may be `/usr/local/` for system-wide installation
of packages, or something like `~/src/prefix` if you want to
have a user-level, local installation path. The latter is
highly recommended for local development, as it allows
compilation and installation without root access.
Any directory may be a prefix, but it is highly recommended
to choose a dedicated directory for this purpose.

Prefixes require a configuration directory to function properly.
Typically, it is called .pybombs/ and is a subdirectory of the prefix.
So, if your prefix is `~/src/prefix`, there will be a directory called
`~/src/prefix/.pybombs/` containing special files. The two most important
files are the inventory file (inventory.yml) and the prefix-local
configuration file (config.yml), but it can also contain recipe files
that are specific to this prefix.

There is no limit to the number of prefixes. Indeed, it may make sense
to have multiple prefixes, e.g. one for system-wide installation, one for
a user-specific installation, and one for cross-compiling to a different
platform.

### Initializing Prefixes

Any directory can function as a prefix, and PyBOMBS will make sure all the
required files and directories are created. However, PyBOMBS provides a way
to initialize a directory to be a full PyBOMBS prefix:

    $ pybombs prefix init /path/to/prefix [-a alias]

This is similar to `git init`. The optional alias allows you to access the
prefix with the alias instead of the full path.

### Aliases

In order to make prefix selection more easy, it is possible to assign names
to prefixes by adding a `[prefix_aliases]` section to a configuration file.
The format is `alias=/path/to/prefix`. Instead of providing the entire path
every time, the alias can be used instead. When running `pybombs prefix init`,
you can use the `--alias` argument to set this automatically.

### Prefix Selection

Prefixes are selected by the following rules, in this order:

1. Whatever is provided by the `-p` or `--prefix` command line switch
2. The current directory
3. The default prefix as defined by the `default_prefix` config switch

If no prefix can be found, most PyBOMBS operations will not be possible,
but some will still work.

### Configuring a prefix' environment (e.g. for cross-compiling)

#### Setting environment variables directly:

In any config file that is read, a `env:` section can be added. This
will set environment variables for any command  (configure, build, make...)
that is run within PyBOMBS.

Note that this will still use the regular system environment as well, but
it will overwrite existing variables. Variable expansion can be used, so
this will keep the original setting:

```{.yml}
env:
    LD_LIBRARY_PATH: ${LD_LIBRARY_PATH}:/path/to/more/libs
```

Note: Because this is a YAML file, remember to separate key/value pairs with
colon (:), not an equals sign, as you would in a shell script.

In all cases, the environment variable `PYBOMBS_PREFIX` is set to the
current prefix, and `PYBOMBS_PREFIX_SRC` is set to the source directory.

#### Using an external script to set the environment

Inside the config section, a shell script can be defined that sets up an
environment, which will then be used for commands running inside this prefix.

Example:

```{.yml}
config:
    # Other vars
    setup_env: /path/to/environment-setup-armv7ahf-vfp-neon-oe-linux-gnueabi
```

## Recipes

### Recipe Format

Recipes files are in YAML format. To write new recipes, the easiest way is to
use other recipes as examples.

Important keys in the recipe files include:

- `inherit`: This will load the values from a template file (`*.lwt`) before
  using the values from the recipe, to set up suitable defaults.
- `category`: Can technically be anything, but certain categories
  carry certain meanings

### Recipe Management

Recipes can be stored in multiple locations, which easily allows to store
separate recipe lists for specific projects.

If the same recipe can be found in more than one location, it will be
chosen from the most specific. The precise order is:
- Recipe locations specified on the command line (Using the `-r` switch)
- From the environment variable `PYBOMBS_RECIPE_DIR`
- The current prefix (if available)
- Global recipe locations

This mechanism can be used to override recipes for certain prefixes. For
example, the `gnuradio.lwr` file could be copied and adapted to use a
different branch than the default recipe does. (Note that specific parts
of recipes can also be overridden in the config.yml file, in the [packages]
section).

Recipe management can be mostly done through the command line using
the `pybombs recipes` command -- editing configuration files is possible,
but often not necessary. Run

    $ pybombs help recipes

for further information on the `pybombs recipes` command.

#### Remote and Local Recipe Locations

Recipe locations can be either local directories (in this case, PyBOMBS will
simply read any .lwr file from this directory, *without* traversing into
subdirectories), or a remote location.
Remote locations can be:
- git repositories
- Remotely stored .tar.gz archives

Remote locations are copied into a local directory, so PyBOMBS can read the .lwr
files locally. During normal operations, PyBOMBS will not try to read the remote
location, so offline usage is still possible.
This local cache of recipes is stored in the same directory as the location of
the corresponding config file (e.g., if `~/.pybombs/config.yml` declares a
recipe called 'myrecipes', the local cache will be in
`~/.pybombs/recipes/myrecipes`).

## Configuration Files

Typically, there are four ways to configure PyBOMBS:

1. The global configuration file (e.g. `/etc/pybombs/config.yml`)
2. The user-local configuration file (e.g. `~/.pybombs/config.yml`)
3. The prefix-local configuration file (e.g. `~/src/prefix/.pybombs/config.yml`)
4. By using the `--config` switch on the command line

Higher numbers mean higher priority. Conflicting options are resolved by
choosing option values with higher priority.

### `config.yml` File Format

The config.yml files are in YAML format. A typical file looks like this:

```{.yml}
# All configuration options:
# (Run `pybombs config` to learn which options are recognized)
config:
	satisfy_order: native,src
	default_prefix: default
	# ... more options

# Prefix aliases:
prefix_aliases:
	default: /home/user/src/pb-prefix/
	sys: /usr/local

# Prefix configuration directories:
prefix_config_dir:
	sys: /home/user/pb-default/
	# Typically, you don't need this, because the prefix configuration
	# directory is in <PREFIX>/.pybombs

# Recipe locations:
recipes:
	myrecipes: /usr/local/share/recipes
	morerecipes: /home/user/pb-recipes
	remoterecipes: git+git://url/to/repo

# Package flags:
packages:
	gnuradio:
		forcebuild: True # This will skip any packagers for this package
                                 # and use a source build
                forceinstalled: False # 'True' will always assume this package is
                                      # installed and skip installing it
                # Any other option here will override whatever's in the
                # corresponding recipe (in this case, gnuradio.lwr)

# Like package flags, but applies flags to all packages
# in a certain category. 'common' is all OOTs.
categories:
	common:
		forcebuild: True # This would force source builds for any package in the
                                 # `common` category

# Environment variables
env:
	LD_LIBRARY_PATH: ${LD_LIBRARY_PATH}:/path/to/more/libs
```

