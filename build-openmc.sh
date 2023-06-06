#!/bin/bash
set -ex

# Build openmc
cd openmc
./tools/ci/gha-install-mcpl.sh
python tools/ci/gha-install.py

# Install the OpenMC python API
pip install .
cd ../
