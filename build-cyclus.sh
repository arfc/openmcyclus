#!/bin/bash
set -ex

# Build cyclus
cd cyclus
git checkout python-api
python install.py
