***************************
Contributing to OpenMCyclus
***************************

Welcome, and thank you for your interest in developing OpenMCyclus. This document 
serves as a guide for making contributions to this archetype library. 

General Notes
=============
OpenMCyclus relies on Cyclus and OpenMC, so familiarity with using both is 
recommended. Please refer to the `Cyclus website <http://fuelcycle.org>`_ and 
`OpenMC documenatation <https://docs.openmc.org/en/v0.14.0/index.html>`_ for 
information about each code.

Contributions to this software are made via GitHub, so familiarity with 
git is recommended. Resources for installing 
and using git and GitHub include:

* The `git website <https://git-scm.com/>`_

* The `GitHub docs <https://docs.github.com/en>`_

* This `tutorial <https://help.github.com/articles/using-pull-requests/>`_ on creating 
  pull requests 

The general steps for contributing to OpenMCyclus are:

1. Create a fork of the OpenMCyclus repository
2. Create a new branch on your fork, keeping the `main` branch clean and 
   up-to-date with the ARFC version of the repository `main` branch
3. Make your desired changes on your new branch
4. Make sure all of the tests pass. You can run the tests locally, or they will 
   run in the CI (via GitHub Actions) when you push changes
5. When you're finished with your changes and the tests pass, update the 
   `CHANGELOG <CHANGELOG.rst>`_ with the changes you've made. 
6. Issue a pull request into the ARFC repository `main` branch.

Reviewing pull requests
=======================
Reviewing pull requests is an important part of development work. When 
reviewing pull requests please:

* Make sure the code is consistent with the `PEP 8 style guide <https://peps.python.org/pep-0008/>`_ 
* Make sure all tests in CI are passing
* Ensure that new tests are added as needed to address new features
* Make positive, constructive comments on the code

Once all conversations are resolved and all tests pass, you are welcome to 
merge the pull request. 

Running tests:
==============
pytest is used for all tests. Tests should be run from the top-level 
directory of this repository using:

  .. code-block:: bash
    
    $ pytest tests/

Releases:
=========
When a new release is ready:

#. Update all documentation as needed and issue a PR for this
#. git tag -a <version>
#. git push upstream main
#. git push upstream <version>