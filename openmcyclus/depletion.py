import numpy as np
import openmc
import openmc.deplete as od
from xml.dom import minidom
import pathlib
import xml.etree.ElementTree as ET
import math

class Depletion(object):
    def __init__(self, path:str, chain_file:str, 
    timesteps:int, power:float, conversion_factor:float=3):
        '''
        Class to hold objects related to calling 
        :class:`~openmc.deplete.IndependentOperator`
        to perform transport-independent depletion.

        Inputs:
        ----------
        path: str
            path to directory containing for OpenMC model (geometry, materials,
            and settings) and the results (depletion_results.h5)
        chain_file: str
            name of file with depletion chain data. Just the file name is
            required, it is assumed that the file is in the same
            location as the other files for the OpenMC model
        timesteps: int
            number of time steps to perform depletion. It is assumed that
            the number given is in units of months. This value is 
            multiplied by 30 to give a timestep in days. 
        power: float
            power output of the reactor, assumed in MWe.
        conversion_factor: float
            conversion factor to go from MWe to MWth. Default value of 3,
            representing a thermal efficiency of 1/3
        '''
        self.path = pathlib.Path(path)
        self.chain_file = chain_file
        self.timesteps = timesteps
        self.power = power
        self.conversion_factor = conversion_factor

    def read_model(self):
        '''
        Read the .xml files in the defined path to create an OpenMC
        model in the python API. The files are assumed to be named
        geometry.xml, materials.xml, settings.xml, and (optionally)
        tallies.xml

        Returns:
        ---------
        model: openmc.model.model object
            OpenMC model of reactor geometry.
        '''
        model_kwargs = {"geometry": (self.path / "geometry.xml"),
                        "materials": (self.path / "materials.xml"),
                        "settings": (self.path / "settings.xml")}
        tallies_path = self.path / "tallies.xml"
        if tallies_path.exists():
            model_kwargs["tallies"] = tallies_path
        model = openmc.model.model.Model.from_xml(**model_kwargs)
        return model
    
    def update_materials(self, comp_list):
        '''
        Read in the material compositions of the fuel assemblies present 
        in the reactor to be transmuted. Then modify the composition of 
        the pre-defined materials to match the compositions from 
        Cyclus. 


        Parameters:
        -----------
        comp_list: list of dicts
            list of the fresh fuel compositions present in the core 
            at the calling of the transmute function.

        Outputs:
        --------
        materials.xml: file 
            updated XML for OpenMC with new compositions

        '''
        openmc_materials = ET.parse(str(self.path / "materials.xml"))
        openmc_root = openmc_materials.getroot()

        for child in openmc_root:
            if '_' in child.attrib['name']:
                underscore_index = child.attrib['name'].index('_')
                assembly_number = child.attrib['name'][underscore_index+1:]
                if child.attrib['name'][:underscore_index] == 'assembly':
                    for material in child.findall('nuclide'):
                        child.remove(material)
                    new_comp = comp_list[int(assembly_number)-1]
                    for nuclide in new_comp:
                        Z = math.floor(nuclide/10000000)
                        A = math.floor((nuclide - Z*10000000)/10000)
                        m = nuclide - Z*10000000 - A*10000
                        nucname = openmc.data.gnd_name(Z,A,m)
                        new_nuclide = f"""<nuclide wo="{str(new_comp[nuclide])}" name="{nucname}" />"""
                        new_nuclide_xml = ET.fromstring(new_nuclide)
                        child.insert(1, new_nuclide_xml)
        ET.indent(openmc_root)
        openmc_materials.write(str(self.path / "materials.xml"))
        return

    def read_microxs(self):
        '''
        Reads .csv file with microscopic cross sections. The
        csv file is assumed to be named "micro_xs.csv". This will need to
        be relative to Cyclus input file location

        Parameters:
        -----------

        Returns:
        --------
        microxs: object
            microscopic cross section data
        '''
        microxs = od.MicroXS.from_csv(str(self.path / "micro_xs.csv"))
        return microxs

    def run_depletion(self):
        '''
        Run the IndependentOperator class in OpenMC to perform
        transport-independent depletion.

        Parameters:
        -----------

        Outputs:
        --------
        depletion_results.h5: database
            HDF5 data base with the results of the depletion simulation
        '''
        model = self.read_model()
        micro_xs = self.read_microxs()
        ind_op = od.IndependentOperator(model.materials, micro_xs,
                                        str(self.path / self.chain_file))
        ind_op.output_dir = self.path
        integrator = od.PredictorIntegrator(ind_op, np.ones(
            self.timesteps*30), power=self.power*1000*self.conversion_factor, 
            timestep_units='d')
        integrator.integrate()

        return

    def create_recipe(self, prototype, recipe_list):
        '''
        Converts the depleted material compositions to an XML file readable
        by cyclus.

        Parameters:
        -----------
        prototype: str
            name of prototype deployed
        recipe_list: list of strs
            names of out recipe for the commodities going into the reactor. This 
            name is applied to the updated recipes. 

        Outputs:
        --------
        {self.path}/{self.prototype}_fuel.xml : XML file
            File containing the depleted material composition in the
            required format for Cyclus. The path and prototype names are read
            in from the class instantiation. Path will need to
            be relative to Cyclus input file location
        '''
        results = od.Results(self.path / "depletion_results.h5")
        #composition = results.export_to_materials(-1, None, "./examples/materials.xml")
        root = ET.Element("recipes")
        for index, material_id in enumerate(['5','6','7']):
            material = results[-1].get_material(material_id)
            recipe = ET.SubElement(root, "recipe")
            name = ET.SubElement(recipe, "name").text = recipe_list[index]
            basis = ET.SubElement(recipe, "basis").text='atom'
            nuclides = ET.SubElement(recipe, "nuclide")
            for nuclide in material.nuclides:
                if nuclide.percent < 1e-15:
                    continue
                Z, A,  m = openmc.data.zam(nuclide.name)
                nuc_id = ET.SubElement(nuclides, "id").text = str(Z*10000000 + A*10000 + m)
                comp = ET.SubElement(nuclides, "comp").text = str(nuclide.percent)
        ET.indent(root)
        tree = ET.ElementTree(root)

        file_name = str(self.path / str(prototype + "_fuel.xml"))
        tree.write(file_name)
        return
