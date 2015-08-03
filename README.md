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

## Prefixes

A prefix is a directory into which packages are installed.
The prefix may be /usr/local/ for system-wide installation
of packages, or something like ~/src/prefix if you want to
have a user-level, local installation path. The latter is
highly recommended for local development, as it allows
compilation and installation without root access.
Any directory may be a prefix, but it is highly recommended
to choose a dedicated directory for this purpose.

Prefixes require a configuration directory to function properly.
Typically, it is called .pybombs/ and is a subdirectory of the prefix.
So, if your prefix is `~/src/prefix`, there will be a directory called
`~/src/prefix/.pybombs/` containing special files. The two most important
files are the inventory file (inventory.dat) and the prefix-local
configuration file (config.dat), but it can also contain recipe files
that are specific to this prefix.

There is no limit to the number of prefixes. Indeed, it may make sense
to have multiple prefixes, e.g. one for system-wide installation, one for
a user-specific installation, and one for cross-compiling to a different
platform.

### Aliases

In order to make prefix selection more easy, it is possible to assign names
to prefixes by adding a `[prefix_aliases]` section to a configuration file.
The format is `alias=/path/to/prefix`. Instead of providing the entire path
every time, the alias can be used instead.

### Prefix Selection

Prefixes are selected by the following rules, in this order:

1. Whatever is provided by the `-p` or `--prefix` command line switch
2. The current directory
3. The default prefix as defined by the `default_prefix` config switch

If no prefix can be found, most PyBOMBS operations will not be possible,
but some will still work.

### Configuring a prefixes environment (cross-compiling)

#### Setting environment variables directly:

In any config file that is read, a `[env]` section can be added. This
will set environment variables for any command  (configure, build, make...)
that is run within PyBOMBS.

Note that this will still use the regular system environment as well, but
it will overwrite existing variables. Variable expansion can be used, so
this will keep the original setting:

    [env]
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/path/to/more/libs

In all cases, the environment variable `PYBOMBS_PREFIX` is set to the
current prefix.

#### Using an external script to set the environment

Inside the config section, a shell script can be defined that sets up an
environment, which will then be used to set up an environment.

Example:

    [config]
    # Other vars
    setup_env=/path/to/environment-setup-armv7ahf-vfp-neon-oe-linux-gnueabi

## Recipes

### Recipe Format

tbw

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
example, the `gnuradio.lwt` file could be copied and adapted to use a
different branch than the default recipe does.

Recipe management can be mostly done through the command line using
the `pybombs recipes` command -- editing configuration files is possible,
but often not necessary. Run

    pybombs help recipes

for further information on the `pybombs recipes` command.

#### Remote and Local Recipe Locations

Recipe locations can be either local directories (in this case, PyBOMBS will
simply read any .lwr file from this directory, without traversing into
subdirectories), or a remote location.
Remote locations can be:
- git repositories
- http locations

Remote locations are copied into a local directory, so PyBOMBS can read the .lwr
files locally. This local cache of recipes are stored in the same directory
as the location of the corresponding config file (e.g., if `~/.pybombs/config.dat`
declare a recipe called 'myrecipes', the local cache will be in
`~/.pybombs/recipes/myrecipes`).

## Configuration Files

Typically, there are four ways to configure PyBOMBS:

1. The global configuration file (e.g. `/etc/pybombs/config.dat`)
2. The local configuration file (e.g. `~/.pybombs/config.dat`)
3. The recipe configuration file (e.g. `~/src/prefix/.pybombs/config.dat`)
4. By using the `--config` switch on the command line

Higher numbers mean higher priority. Conflicting options are resolved by
choosing option values with higher priority.

### `config.dat` File Format

The config.dat files are of the standard INI file format. A typical file
looks like this:

```
# All configuration options:
[config]
satisfy_order = native,src
default_prefix=default
# ... more options

# Prefix aliases:
[prefix_aliases]
default=/home/user/src/pb-prefix/
sys=/usr/local

# Prefix configuration directories:
[prefix_config_dir]
sys=/home/user/pb-default/
# Typically, you don't need this, because the prefix configuration
# directory is in <PREFIX>/.pybombs

# Recipe locations:
[recipes]
myrecipes=/usr/local/share/recipes
morerecipes=/home/user/pb-recipes
remoterecipes=git+git://url/to/repo

# Package flags:
[packages]
gnuradio=forcebuild

# Like package flags, but applies flags to all packages
# in a certain category. 'common' is all OOTs.
[categories]
common=forcebuild

# Environment variables
[env]
LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/path/to/more/libs
```

