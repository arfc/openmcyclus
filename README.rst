OpenMCyclus
------------
.. image:: https://github.com/arfc/openmcyclus/actions/workflows/test-openmcyclus.yml/badge.svg?branch=main

Library of Cyclus archetypes to couple Cyclus with OpenMC.

Installation 
============

Dependencies
~~~~~~~~~~~~

You will need to have `Cyclus <https://fuelcycle.org/>`_, `OpenMC <https://docs.openmc.org>`_, 
and their required dependencies. Both are available via conda binaries. Please note 
the versions listed below, as these are required versions, not minimum versions. 

+---------+---------+
| Package | Version |
+=========+=========+
| Cyclus  | 1.6     |
+---------+---------+
| OpenMC  | 0.14    |
+---------+---------+

Directions to install Cyclus and OpenMC [1]_ 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash
  
    conda install -y openssh gxx_linux-64=12.2 gcc_linux-64=12.2 cmake make docker-pycreds git xo python-json-logger python=3.10 glibmm glib libxml2 libxmlpp libblas libcblas liblapack pkg-config coincbc boost-cpp sqlite pcre gettext bzip2 xz setuptools pytest pytables pandas jinja2 cython=0.29 websockets pprintpp hdf5=1.12.2 notebook nb_conda_kernels requests entrypoints pyyaml vtk coverage pytest-cov colorama libpng uncertainties lxml scipy

    HDF5_DIR=$CONDA_PREFIX \
    pip install --upgrade-strategy only-if-needed --no-binary=h5py h5py

    git clone https://github.com/cyclus/cyclus.git

    cd cyclus

    git checkout python-api

    python install.py

    cd ../
    git clone --recurse-submodules https://github.com/openmc-dev/openmc.git
    cd openmc/

    mkdir build && cd build

    cmake ..

    make

    sudo make install

    cd ../

    pip install .

If desired, Cycamore can be installed from `here <https://github.com/cyclus/cyclus>`_. 
Cycamore is *highly* recommended, as it contains other archetypes for creating a 
fuel cycle model in Cyclus, but it is not a dependency for OpenMCyclus. 

Install OpenMCyclus
~~~~~~~~~~~~~~~~~~~

To install OpenMCyclus:

.. code-block:: bash

    ~ $ git clone https://github.com/arfc/openmcyclus.git 

    ~ $ cd openmcyclus

    ~/openmcyclus/ $ pip install .


To run the tests:

.. code-block:: bash

    ~/openmcyclus $ pytest tests/


Running
=======

This archetype assumes that you have a defined reactor model in OpenMC (``.xml``) 
files and the required microscopic cross sections (``.csv`` file) for the model. 
The cross section data must be saved as a ``.csv`` file. These files must 
all be in the same location. Information about these can be found on the 
`OpenMC docpages <https://docs.openmc.org>`_. 

This archetype is then called during a Cyclus simulation by calling 
the ``DepleteReactor`` archetype from the ``openmcyclus.DepleteReactor`` 
library. The input structure is:

  .. code_block:: XML

        <DepleteReactor>
          <fuel_incommods>
            <val>string</val>
            ...
            <val>string</val>
          </fuel_incommods>
          <fuel_prefs>
            <val>double</val>
            ...
            <val>double</val>
          </fuel_prefs>
          <fuel_outcommods>
            <val>string</val>
            ...
            <val>string</val>
          </fuel_outcommods>
          <fuel_inrecipes>
            <val>string</val> 
            ...
            <val>string</val>
          </fuel_inrecipes>
          <fuel_outrecipes>
            <val>string</val> 
            ...
            <val>string</val>
          </fuel_outrecipes>
          <assem_size>double</assem_size>
          <cycle_time>int</cycle_time>
          <refuel_time>int</refuel_time>
          <n_assem_core>int</n_assem_core>
          <n_assem_batch>int</n_assem_batch>
          <power_cap>double</power_cap>
          <model_path>string</model_path>
          <chain_file>string</chain_file>
        </DepleteReactor>

Some notes about this input structure:

- ``fuel_prefs`` and ``fuel_inrecipes`` must be equal in length to 
  ``fuel_incommods`` and ``fuel_outrecipes`` must be equal in length to ``fuel_outcommods``. 

- The ``model_path`` variable is the location of the files for OpenMC (can be 
  relative or absolute path): one-group cross sections, materials, and depletion 
  chain file. If using a relative path, it must be relative to the directory you are 
  running the Cyclus input file from, not the location of the file that defines the 
  prototype. 

- The archetype assumes that 
  the OpenMC materials are in the file called ``materials.xml`` and that the cross 
  section data is in a file called ``micro_xs.csv``. 

- The ``chain_file`` variable 
  is the depletion chain file, and the user provides the name of this file. 

- Each material in the ``materials.xml`` file that are fuel materials must 
  be marked as ``depletable`` and have the name ``assembly_#``. Define one material 
  for each assembly in the reactor core (matches with ``n_assem_core``),  
  the number assigned to each material name is irrelevant, just as long as  
  there is one. 

Outputs
~~~~~~~
The results of the simulation will be written to `cyclus.sqlite`
or the file name provided when Cyclus was called. 

.. [1] Directions on OpenMC install from source taken from:
  https://docs.openmc.org/en/stable/quickinstall.html, consult this
  page for the most up to date instructions. 