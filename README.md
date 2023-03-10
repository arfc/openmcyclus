# OpenMCyclus
![Build Status](https://github.com/arfc/openmcyclus/actions/workflows/test-openmcyclus.yml/badge.svg?branch=main)

Repository of [Cyclus](https://fuelcycle.org/) archetypes to couple Cyclus with [OpenMC](https://docs.openmc.org/en/develop/pythonapi/generated/openmc.run.html)

## Installation 
To install this archetype library run ``pip install .``. 
To run tests: ``pytest`` from the main directory.

### Dependencies
You will need to have [Cyclus](www.github.com/cyclus/cyclus), [OpenMC](https://docs.openmc.org).
and their required dependencies. Install both of these in the same conda environment.

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
