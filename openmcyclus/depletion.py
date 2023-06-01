import numpy as np
import openmc
import openmc.deplete as od
from xml.dom import minidom
import pathlib
import xml.etree.ElementTree as ET

class Depletion(object):
    def __init__(self, path:str, prototype:str, chain_file:str, 
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
        prototype: str
            name of prototype undergoing depletion
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
        self.prototype = prototype
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
        print("updating materials")
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
                        new_nuclide = f"""<nuclide ao="{str(new_comp[nuclide])}" name="{str(nuclide)}" />"""
                        new_nuclide_xml = ET.fromstring(new_nuclide)
                        child.insert(1, new_nuclide_xml)
        openmc_material.write(str(self.path / "materials.xml"))

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
        microxs = od.MicroXS.from_csv(self.path / "micro_xs.csv")
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

    def create_recipe(self):
        '''
        Converts the depleted material compositions to an XML file readable
        by cyclus.

        Parameters:
        -----------

        Outputs:
        --------
        {self.path}/{self.prototype}_fuel.xml : XML file
            File containing the depleted material composition in the
            required format for Cyclus. The path and prototype names are read
            in from the class instantiation. Path will need to
            be relative to Cyclus input file location
        '''
        results = od.Results(self.path / "depletion_results.h5")
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
        file_name = str(self.path / str(self.prototype + "_fuel.xml"))
        with open(file_name, "w") as f:
            f.write(xml_str)
        return
