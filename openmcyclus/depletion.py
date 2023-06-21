import numpy as np
import openmc
import openmc.deplete as od
from xml.dom import minidom
import pathlib
import xml.etree.ElementTree as ET
import math


class Depletion(object):
    def __init__(self, chain_file: str,
                 timesteps: int, power: float, conversion_factor: float = 3):
        '''
        Class to hold objects related to calling
        :class:`~openmc.deplete.IndependentOperator`
        to perform transport-independent depletion.

        Parameters:
        -----------
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
        self.chain_file = chain_file
        self.timesteps = timesteps
        self.power = power
        self.conversion_factor = conversion_factor

    def read_model(self, path):
        '''
        Read the .xml files in the defined path to create an OpenMC
        model in the python API. The files are assumed to be named
        geometry.xml, materials.xml, settings.xml, and (optionally)
        tallies.xml

        Parameters:
        -----------
        path: str
            path of directory holding the files for/from OpenMC

        Returns:
        ---------
        model: openmc.model.model object
            OpenMC model of reactor geometry.
        '''
        model_kwargs = {"geometry": path + "geometry.xml",
                        "materials": path + "materials.xml",
                        "settings": path + "settings.xml"}
        model = openmc.model.model.Model.from_xml(**model_kwargs)
        return model

    def update_materials(self, comp_list, path):
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
        path: str
            path of directory holding the files for/from OpenMC

        Returns:
        --------
        material_ids: list of strs
            material id numbers for the OpenMC model

        Outputs:
        --------
        materials.xml: file
            updated XML for OpenMC with new compositions

        '''
        openmc_materials = ET.parse(str(path + "materials.xml"))
        openmc_root = openmc_materials.getroot()
        material_ids = []

        for child in openmc_root:
            if '_' in child.attrib['name']:
                underscore_index = child.attrib['name'].index('_')
                assembly_number = child.attrib['name'][underscore_index + 1:]
                material_ids.append(child.attrib['id'])
                if child.attrib['name'][:underscore_index] == 'assembly':
                    for material in child.findall('nuclide'):
                        child.remove(material)
                    new_comp = comp_list[int(assembly_number) - 1]
                    for nuclide in new_comp:
                        Z = math.floor(nuclide / int(1e7))
                        A = math.floor((nuclide - Z * int(1e7)) / int(1e4))
                        m = nuclide - Z * int(1e7) - A * int(1e4)
                        nucname = openmc.data.gnd_name(Z, A, m)
                        new_nuclide = f"""<nuclide wo="{str(new_comp[nuclide]*100)}" name="{nucname}" />"""
                        new_nuclide_xml = ET.fromstring(new_nuclide)
                        child.insert(1, new_nuclide_xml)
        ET.indent(openmc_root)
        openmc_materials.write(str(path + "materials.xml"))
        return material_ids

    def read_microxs(self, path):
        '''
        Reads .csv file with microscopic cross sections. The
        csv file is assumed to be named "micro_xs.csv". This will need to
        be relative to Cyclus input file location

        Parameters:
        -----------
        path: str
            path of directory holding the files for/from OpenMC        

        Returns:
        --------
        microxs: object
            microscopic cross section data
        '''
        microxs = od.MicroXS.from_csv(str(path + "micro_xs.csv"))
        return microxs

    def run_depletion(self, path):
        '''
        Run the IndependentOperator class in OpenMC to perform
        transport-independent depletion.

        Parameters:
        -----------        
        path: str
            path of directory holding the files for/from OpenMC

        Outputs:
        --------
        depletion_results.h5: database
            HDF5 data base with the results of the depletion simulation
        '''
        model = self.read_model(path)
        micro_xs = self.read_microxs(path)
        ind_op = od.IndependentOperator(model.materials, micro_xs,
                                        str(path + self.chain_file))
        ind_op.output_dir = path
        integrator = od.PredictorIntegrator(
            ind_op,
            np.ones(
                self.timesteps *
                30),
            power=self.power *
            1000 *
            self.conversion_factor,
            timestep_units='d')
        integrator.integrate()

        return

    def get_spent_comps(self, material_ids, path):
        '''
        Creates a list of each of the spent fuel compositions from the 
        OpenMC depletion

        Parameters:
        -----------
        material_id: list of strs
            material ids for the assembly materials in the OpenMC model
        path: str
            path of directory holding the files for/from OpenMC

        Returns:
        --------
        spent_comps: list of dicts
            list of the compositions from the OpenMC model
        '''
        results = od.Results(path + "depletion_results.h5")
        spent_comps = []
        for index, material_id in enumerate(material_ids):
            material = results[-1].get_material(material_id)
            comp = {}
            for nuclide in material.nuclides:
                if nuclide.percent < 1e-15:
                    continue
                Z, A, m = openmc.data.zam(nuclide.name)
                comp.update({Z*int(1e7)+A*int(1e4) + m :nuclide.percent/100})
            spent_comps.append(comp)
        return spent_comps
