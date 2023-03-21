# OpenMCyclus
![Build Status](https://github.com/arfc/openmcyclus/actions/workflows/test-openmcyclus.yml/badge.svg?branch=main)

Repository of [Cyclus](https://fuelcycle.org/) archetypes to couple Cyclus with [OpenMC](https://docs.openmc.org/en/develop/pythonapi/generated/openmc.run.html)

## Installation 


### Dependencies
You will need to have [Cyclus](www.github.com/cyclus/cyclus), [OpenMC](https://docs.openmc.org).
and their required dependencies. It is recommended to install Cyclus from source,
then install OpenMC in a separate conda environment as their python dependencies 
clash when both are installed via conda in the same environment.

conda install -y python=3.7 cyclus cycamore hdf5 coincbc=2.9 gettext jinja2 libxml2 libxmlpp nose pytest pcre websockets xz libgfortran4 cython matplotlib notebook nb_conda_kernels pandas requests entrypoints pyyaml vtk coverage pytest-cov colorama gcc_linux-64=12.2 gxx_linux-64=12.2 libpng cmake make

pip install --upgrade-strategy only-if-needed --no-binary=h5py h5py

git clone --recurse-submodules https://github.com/openmc-dev/openmc.git

cd openmc/

mkdir build && cd build

cmake ..

make

sudo make install

cd ../

pip install .


### Install OpenMCyclus
To install this archetype library run ``pip install .``. 
To run tests: ``pytest`` from the main directory.

### Running
This archetype assumes that you have a defined reactor model in OpenMC (``.xml``) 
files and the 
required microscopic cross sections (``.csv`` file) for the model. The 
cross 
section data must be saved as a ``.csv`` file. These files must 
all be in the same location. Information about 
these can be found on the [OpenMC docpages](https://docs.openmc.org). 

This archetype is then called during a Cyclus simulation by calling 
the ``DepleteReactor`` archetype from the ``openmcyclus.DepleteReactor`` 
library. The input structure is:

    <DepleteReactor/>

### Outputs
The compositions for the spent fuel are saved to an ``.xml`` file named 
``prototype_fuel.xml`` in which ``prototype`` is the prototype name in 
the Cyclus simulation
