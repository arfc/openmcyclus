#!/usr/bin/env python
from distutils.core import setup


VERSION = '0.1.0'
setup_kwargs = {
    "version": VERSION,
    "description": 'Cyclus Archetypes Coupled with OpenMC',
    "author": 'Amanda M. Bachmann',
    }

if __name__ == '__main__':
    setup(
        name='openmcyclus',
        packages=["openmcyclus"],
        **setup_kwargs
        )
