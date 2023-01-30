import numpy as np
import openmc
import openmc.deplete as od
from xml.dom import minidom

def read_model(path):
    '''
    Read the .xml files in the defined path to create an OpenMC 
    model in the python API. The files are assumed to be named 
    geometry.xml, materials.xml, settings.xml, and (optionally) 
    tallies.xml

    Parameters:
    -----------
    path: str
        path to directory with files for OpenMC model. This will need to 
        be relative to Cyclus input file location
    
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
    csv file is assumed to be named "micro_xs.csv". This will need to 
        be relative to Cyclus input file location

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
        path to directory with files for OpenMC. This will need to 
        be relative to Cyclus input file location
    chain_file: str
        name (and path, if needed) of decay chain file for OpenMC
        to read. 
    timesteps: int
        number of timesteps (days) the reactor operates, will want to read 
        this in from DepleteReactor.cycle_length, then multiple by days/month
    power: float
        power (W) of the reactor model. Read in from DepleteReactor.power_cap

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
        path to depletion results file. This will need to 
        be relative to Cyclus input file location
    recipe_name: str 
        name of recipe in the Cyclus simulation. Maybe prototype name?
        Something easy to get from elsewhere in the simulation
    output_path: str
        path to save the output file to, relative to cyclus input
         files 
    Outputs:
    --------
    output_path/recipe_name.xml : XML file
        File containing the depleted material composition in the 
        required format for Cyclus. Path will need to 
        be relative to Cyclus input file location
    '''
    results = od.Results.from_hdf5(str(path + "depletion_results.h5"))
    composition = results.export_to_materials(-1)
    root = minidom.Document()
    recipe = root.createElement('recipes')
    root.appendChild(recipe)
    for index, material in enumerate(composition):
        material_recipe = root.createElement('recipe')
        name = root.createElement('name')
        basis = root.createElement('basis')
        
        name_text = root.createTextNode(material.name)
        basis_text = root.createTextNode('atom')
        
        name.appendChild(name_text)
        basis.appendChild(basis_text)
        material_recipe.appendChild(name)
        material_recipe.appendChild(basis)
        for item in composition[index].nuclides:
            nuclide = root.createElement('nuclide')
            nuclide_id = root.createElement('id')
            nuclide_comp = root.createElement('comp')
            
            id_text = root.createTextNode(item.name)
            comp_text = root.createTextNode(str(item.percent))

            nuclide_id.appendChild(id_text)
            nuclide_comp.appendChild(comp_text)
            nuclide.appendChild(nuclide_id)
            nuclide.appendChild(nuclide_comp)
            material_recipe.appendChild(nuclide)
        recipe.appendChild(material_recipe)
    xml_str = root.toprettyxml(newl='\n')
    with open("uox.xml", "w") as f:
        f.write(xml_str)
    return
