# PyBOMBS Commands

To add sub-commands to PyBOMBS, do the following:

1) Add a module for the subcommand. The filename is not strictly
   important, but convention is to make the filename and the
   command the same.
2) Add a command class in that file that derives from CommandBase.
   See other command classes for example. At minimum, it requires an
   argument sub-parser, a cmds dictionary, and a run() method.
3) Import that class in this directory's `__init__.py` file.

