import numpy as np
import openmc
import openmc.deplete as od
import xml.etree.ElementTree as ET
import math


class Depletion(object):
    def __init__(self, chain_file: str,
                 timesteps: int, power: float,
                 path: str):
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
            power output of the reactor, assumed in MWth.
        path: str
            relative path to micro xs and materials files

        Attributes:
        -----------
        chain_file: str
            file name for decay chain data
        timesteps: int
            number of time steps to perform depletion. It is assumed that
            the number given is in units of months. This value is
            multiplied by 30 to give a timestep in days.
        power: float
            power output of the reactor, assumed in MWth.
        path: str
            relative path to micro xs and materials files

        '''
        self.chain_file = chain_file
        self.timesteps = timesteps
        self.power = power
        self.path = path

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
        materials: openmc.Materials
            materials object to be depleted

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

    def run_depletion(self, flux, materials, microxs):
        '''
        Run the IndependentOperator class in OpenMC to perform
        transport-independent depletion. This method is only 
        used in the test suite, and not in the OpenMCyclus 
        archetype

        Parameters:
        -----------        
        flux: float
            flux through nuclear fuel
        materials: openmc.Materials()
            material definitions to deplete
        microxs: openmc.deplete.MicroXS
            microscopic cross section data

        Outputs:
        --------
        depletion_results.h5: database
            HDF5 data base with the results of the depletion simulation
        '''
        ind_op = od.IndependentOperator(materials,
                                        [np.array([flux])]*len(materials),
                                        [microxs]*len(materials),
                                        str(self.path + self.chain_file))
        ind_op.output_dir = self.path
        integrator = od.PredictorIntegrator(
            ind_op,
            np.ones(self.timesteps)*30,
            power=self.power *
            1e6,
            timestep_units='d')
        integrator.integrate()

        return

    def get_spent_comps(self, material_ids, microxs):
        '''
        Creates a list of each of the spent fuel compositions from the 
        OpenMC depletion

        Parameters:
        -----------
        material_id: list of strs
            material ids for the assembly materials in the OpenMC model

        Returns:
        --------
        spent_comps: list of dicts
            list of the compositions from the OpenMC model
        '''
        results = od.Results(self.path + "depletion_results.h5")
        nuclides = microxs.nuclides
        spent_comps = []
        for material_id in material_ids:
            comp = {}
            for nuclide in nuclides:
                Z, A, m = openmc.data.zam(nuclide)
                mass = results.get_mass(str(material_id), nuclide)[-1][-1]
                if mass <= 1e-10:
                    continue
                comp.update({Z*int(1e7)+A*int(1e4) + m :mass})
            spent_comps.append(comp)
        return spent_comps
