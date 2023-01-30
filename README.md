# openmcyclus
Repository of [Cyclus](https://fuelcycle.org/) archetypes to couple Cyclus with [OpenMC](https://docs.openmc.org/en/develop/pythonapi/generated/openmc.run.html)

## Installation 
To install this archetype library run ``pip install .``. Testing 
to be added soon.
To run tests: ``pytest`` from the main directory.

### Dependencies
You will need to have [Cyclus](www.github.com/cyclus/cyclus), [OpenMC](https://docs.openmc.org).
and their required dependencies. Install both of these in the same conda environment.

### Running
This archetype assumes that you have a defined reactor model in OpenMC (``.xml``) 
files and the 
required microscopic cross sections for the model. Information about 
these can be found on the [OpenMC website](https://docs.openmc.org). The cross 
section data must be saved as a ``.csv`` file. 

### Outputs
The compositions for the spent fuel are saved to an ``.xml`` file named after 
the recipe name in the |Cyclus| simulation.
