import numpy as np
import openmc
import openmc.deplete as od
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

    def read_materials(self, path):
        '''
        Read in the materials file for OpenMC

        Parameters:
        -----------
        path: str
            path to the materials.xml file

        Returns:
        ---------
        materials: openmc.material object
            Materials for OpenMC
        '''
        materials = openmc.Materials()
        materials = materials.from_xml(str(path + "/materials.xml"))
        return materials


    def update_materials(self, comp_list, materials):
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
        material_ids = []
        for index, material in enumerate(materials):
            if 'assembly_' in material.name:
                material_ids.append(material.id)
                material.nuclides.clear()
                for nuclide, percent in comp_list[index].items():
                    Z = math.floor(nuclide / int(1e7))
                    A = math.floor((nuclide - Z * int(1e7)) / int(1e4))
                    m = nuclide - Z * int(1e7) - A * int(1e4)
                    nucname = openmc.data.gnds_name(Z, A, m)
                    material.add_nuclide(nucname, percent, percent_type='wo')
        mats = materials

        return material_ids, mats

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
            1e6*
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
            total_weight = 0
            spent_comp = results[-1].get_material(str(material_id))
            for nuclide in spent_comp.nuclides:
                if nuclide.percent < 1e-10:
                    continue
                total_weight += nuclide.percent*openmc.data.atomic_mass(nuclide.name)
            comp = {}
            for nuclide in spent_comp.nuclides:
                if nuclide.percent < 1e-10:
                    continue
                Z, A, m = openmc.data.zam(nuclide.name)
                weight_frac = (nuclide.percent*openmc.data.atomic_mass(nuclide.name))/total_weight
                comp.update({Z*int(1e7)+A*int(1e4) + m :weight_frac})
            spent_comps.append(comp)
        return spent_comps
