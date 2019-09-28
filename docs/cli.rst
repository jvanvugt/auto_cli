auto_cli's Command-Line Interface
=================================

Registering an app
------------------

::

    usage: ac [-h] --name NAME [--location LOCATION]

    register_app: Register an app with auto_cli

    required arguments:
     --name NAME          Name of the app

    optional arguments:
     --location LOCATION  Parent directory of the auto_cli.py file.

Example:
::

    $ ac cli register_app --name my_app

Listing all registered apps
---------------------------

::

    usage: ac [-h]

    apps: Get all registered apps

Example:
::

    $ ac cli apps
    ['cli']

Deleting an app
---------------

::

    usage: ac [-h] --name NAME

    delete_app: Delete the app

    required arguments:
     --name NAME  Name of the app

Example:
::

    $ ac cli delete_app --name my_app
    Deleted my_app

Listing registered commands
---------------------------

::

    usage: ac APP

    positional arguments:
     APP Name of the app

Example:
::

    $ ac cli
    No command given. Available commands:
    apps            Get all registered apps
    register_app    Register an app with auto_cli
    delete_app      Delete the app
