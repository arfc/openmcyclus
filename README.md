# OpenMCyclus
![Build Status](https://github.com/arfc/openmcyclus/actions/workflows/test-openmcyclus.yml/badge.svg?branch=main)

Repository of [Cyclus](https://fuelcycle.org/) archetypes to couple Cyclus with [OpenMC](https://docs.openmc.org/en/develop/pythonapi/generated/openmc.run.html)

## Installation 
To install this archetype library run ``pip install .``. 
To run tests: ``pytest`` from the main directory.

### Dependencies
You will need to have [Cyclus](www.github.com/cyclus/cyclus), [OpenMC](https://docs.openmc.org).
and their required dependencies. It is recommended to install Cyclus from source,
then install OpenMC in a separate conda environment as their python dependencies 
clash when both are installed via conda in the same environment.

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

    <DepleteReactor>
      <fuel_incommods>
        <val>string</val>
        ...
        <val>string<val>
      </fuel_incommods>
      <fuel_prefs>
        <val>double</val>
        ...
        <val>double<val>
      </fuel_prefs>
      <fuel_outcommods>
        <val>string</val>
        ...
        <val>string<val>
      </fuel_outcommods>
      <fuel_inrecipes>
        <val>string</val> 
        ...
        <val>string<val>
      </fuel_inrecipes>
      <fuel_outrecipes>
        <val>string</val> 
        ...
        <val>string<val>
      </fuel_outrecipes>
      <assem_size>double<assem_size>
      <cycle_time>int</cycle_time>
      <refuel_time>int</refuel_time>
      <n_assem_core>int</n_assem_core>
      <n_assem_batch>int</n_assem_batch>
      <power_cap>double</power_cap>
    </DeployReactor>

The `fuel_prefs`, `fuel_inrecipes` and `fuel_outrecipes` state variables are optional, but 
must be of equal length to the `fuel_incommods` or `fuel_outcommods`.


### Outputs
The compositions for the spent fuel are saved to an ``.xml`` file named 
``prototype_fuel.xml`` in which ``prototype`` is the prototype name in 
the Cyclus simulation
