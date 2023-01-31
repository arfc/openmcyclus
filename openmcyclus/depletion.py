import numpy as np
import openmc
import openmc.deplete as od
import os
from xml.dom import minidom


class Depletion(object):
    def __init__(self, path, prototype, chain_file, timesteps, power):
        '''
        Class to hold objects related to calling the IndependentOperator
        in OpenMC to perform stand alone depletion.

        Inputs:
        ----------
        path: str
            path to file for OpenMC model (geometry, materials,
            and settings) and the results (depletion_results.h5)
        prototype: str
            name of prototype undergoing depletion
        chain_file: str
            name of file with decay chain data. Just the file name is
            required, it is assumed that the file is in the same
            location as the other files for the OpenMC model
        timesteps: int
            number of time steps to perform irradiation. It is assumed that
            the number given is in units of months.
        power: int
            power output of the reactor, assumed in MWe.
        '''
        self.path = path
        self.prototype = prototype
        self.chain_file = chain_file
        self.timesteps = timesteps
        self.power = power

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
        model = openmc.Model.from_xml(
            geometry=str(
                self.path +
                "geometry.xml"),
            materials=str(
                self.path +
                "materials.xml"),
            settings=str(
                self.path +
                "materials.xml"))
        return model

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
        microxs = od.MicroXS.from_csv(str(self.path + "micro_xs.csv"))
        return microxs

    def run_depletion(self):
        '''
        Run the IndependentOperator class in OpenMC to perform
        stand-alone depletion.

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
                                        str(self.path + self.chain_file))
        integrator = od.PredictorIntegrator(ind_op, np.ones(
            self.timesteps), power=self.power, timestep_units='d')
        integrator.integrate()
        os.system(
            'mv ./depletion_results.h5 ' +
            self.path +
            "depletion_results.h5")
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
        results = od.Results.from_hdf5(str(self.path + "depletion_results.h5"))
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
        file_name = str(self.path + self.prototype + "_fuel.xml")
        with open(file_name, "w") as f:
            f.write(xml_str)
        return
