import numpy as np
import pytest
import xml.etree.ElementTree as ET
import unittest
import openmc
import openmc.deplete as od
import pandas as pd
from openmcyclus.depletion import Depletion
import os


class TestDepletion(unittest.TestCase):
    def setUp(self):
        '''
        Set up the instantiation of the Deplete class
        '''
        self.deplete = Depletion(
            "chain_endfb71_pwr.xml",
            10,
            100e-6,
            "./examples/")
        self.materials = openmc.Materials().from_xml(
            "./examples/materials.xml")
        self.micro_xs = od.MicroXS.from_csv("./examples/micro_xs.csv")

    def run_depletion(self, flux):
        '''
        Run the IndependentOperator class in OpenMC to perform
        transport-independent depletion.

        Parameters:
        -----------
        flux: float
            flux through nuclear fuel

        Outputs:
        --------
        depletion_results.h5: HDF5 database
            HDF5 data base with the results of the depletion simulation
        '''
        ind_op = od.IndependentOperator(self.materials,
                                        [np.array([flux])] * len(self.materials),
                                        [self.micro_xs] * len(self.materials),
                                        str(self.deplete.path + self.deplete.chain_file))
        ind_op.output_dir = self.deplete.path
        integrator = od.PredictorIntegrator(
            ind_op,
            np.ones(self.deplete.timesteps) * 30,
            power=self.deplete.power *
            1e6,
            timestep_units='d')
        integrator.integrate()

        return

    def test_update_materials(self):
        '''
        Test that the provided compositions get written to the
        materials.xml file correctly.
        '''
        comps = [{922350000: 0.05, 922380000: 0.95},
                 {551370000: 0.1, 360850000: 0.8, 541350000: 0.1},
                 {942390000: 0.10, 942410000: 0.9}]
        material_ids, materials = self.deplete.update_materials(
            comps, self.materials)
        assert materials[0].nuclides == [
            openmc.material.NuclideTuple('U235', 0.05, 'wo'),
            openmc.material.NuclideTuple('U238', 0.95, 'wo')]
        assert materials[1].nuclides == [
            openmc.material.NuclideTuple('Cs137', 0.1, 'wo'),
            openmc.material.NuclideTuple('Kr85', 0.80, 'wo'),
            openmc.material.NuclideTuple('Xe135', 0.10, 'wo')]
        assert materials[2].nuclides == [
            openmc.material.NuclideTuple('Pu239', 0.10, 'wo'),
            openmc.material.NuclideTuple('Pu241', 0.90, 'wo')]
        assert material_ids == [5, 6, 7]

    def test_run_depletion(self):
        '''
        Test the run_depletion method, which is only used in the test suite.
        This test makes sure that the depletion runs with the correct
        output file created.
        '''
        self.run_depletion(10.3)
        assert os.path.isfile('examples/depletion_results.h5')
        os.system('rm examples/depletion_results.h5')

    def test_get_spent_comps(self):
        '''
        Test the compositions that are returned from running depletion.
        First, the materials are defined and then depletion is run to prevent
        having to store an HDF5 database in the repo
        '''
        self.run_depletion(10.3)
        spent_comps = self.deplete.get_spent_comps(
            ['5', '6', '7'], self.micro_xs)
        assert 551370000 in spent_comps[0].keys()
        assert 922350000 in spent_comps[0].keys()
        assert 932410000 not in spent_comps[0].keys()
        assert spent_comps[0][922350000] == pytest.approx(
            10.650004036820036, rel=1e-5)
        assert spent_comps[0][942390000] == pytest.approx(
            0.22663550016678385, rel=1e-5)
