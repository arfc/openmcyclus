import numpy as np
import openmc
import openmc.deplete as od

def read_model(path):
    '''
    Read the .xml files in the defined path to create an OpenMC 
    model in the python API. The files are assumed to be named 
    geometry.xml, materials.xml, settings.xml, and (optionally) 
    tallies.xml

    Parameters:
    -----------
    path: str
        path to directory with files for OpenMC model.
    
    Returns:
    model: openmc.model.model object
        OpenMC model of reactor geometry.
    '''
    model = openmc.Model.from_xml(geometry = str(path + "geometry.xml"),
                                  materials = str(path + "materials.xml"),
                                  settings = str(path + "materials.xml"))
    return model

def read_microxs(path):
    '''
    Reads .csv file with microscopic cross sections. The 
    csv file is assumed to be named "micro_xs.csv"

    Parameters:
    -----------
    path: str 
        path to csv file
    
    Returns:
    --------
    microxs: object
        microscopic cross section data
    '''
    microxs = od.MicroXS.from_csv(str(path + "micro_xs.csv"))
    return microxs

def run_depletion(path, chain_file, timesteps, power):
    '''
    Run the IndependentOperator class in OpenMC to perform 
    stand-alone depletion.

    Parameters:
    -----------
    path: str 
        path to directory with files for OpenMC
    chain_file: str
        name (and path, if needed) of decay chain file for OpenMC
        to read. 
    timesteps: int
        number of timesteps (days) the reactor operates
    power: float
        power (W) of the reactor model

    Outputs:
    --------
    depletion_results.h5: database
        HDF5 data base with the results of the depletion simulation
    '''
    model = read_model(path)
    micro_xs = read_microxs(path)
    ind_op = od.IndependentOperator(model.materials, micro_xs, chain_file)
    integrator = od.PredictorIntegrator(ind_op, np.ones(timesteps), 
                                        power = power, timestep_units = 'd')
    integrator.integrate()
    return

def create_recipe(path, recipe_name, output_path):
    '''
    Converts the depleted material compositions to an XML file readable 
    by cyclus.
    
    Parameters:
    -----------
    path: str 
        path to depletion results file
    recipe_name: str 
        name of recipe in the Cyclus simulation
    output_path: str
        path to save the output file to
    Outputs:
    --------
    output_path/recipe_name.xml : XML file
        File containing the depleted material composition in the 
        required format for Cyclus
    '''
    return
