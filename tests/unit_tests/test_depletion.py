import numpy as np
import pytest
import xml.etree.ElementTree as ET
import unittest
import openmc
import pandas as pd
from openmcyclus.depletion import Depletion
import pathlib


class TestDepletion(unittest.TestCase):
    def setUp(self):
        '''
        Set up the instantiation of the Deplete class
        '''
        self.deplete = Depletion(
            "examples/", 'Reactor', "chain_endfb71_pwr.xml", 10, 100)

    def test_read_materials(self):
        '''
        Test when the material file is found
        '''
        materials = self.deplete.read_materials()
        assert isinstance(materials, openmc.material.Materials)
        assert materials[0].id == 5
        assert materials[0].name == 'assembly_1'
        assert materials[0].temperature == 900.0

    def test_update_materials(self):
        '''
        Test that the provided compositions get written to the 
        materials.xml file correctly. 
        '''
        comps = [{922350000:0.05, 922380000:0.95}, 
                 {551370000:0.1, 360850000:0.8, 541350000:0.1}, 
                 {942390000:0.10, 942410000:0.9}]
        material_ids = self.deplete.update_materials(comps)
        materials = self.deplete.read_materials()
        assert materials[0].nuclides == [openmc.material.NuclideTuple('U238',95.0, 'wo'), 
                                         openmc.material.NuclideTuple('U235',5.0, 'wo')]
        assert materials[1].nuclides == [openmc.material.NuclideTuple('Xe135',10.0, 'wo'),
                                         openmc.material.NuclideTuple('Kr85',80.0, 'wo'),
                                         openmc.material.NuclideTuple('Cs137',10.0, 'wo')]
        assert materials[2].nuclides == [openmc.material.NuclideTuple('Pu241',90.0, 'wo'), 
                                         openmc.material.NuclideTuple('Pu239',10.0, 'wo')]
        assert material_ids == ['5','6','7']

    def test_read_microxs(self):
        microxs = self.deplete.read_microxs()
        assert isinstance(microxs, pd.DataFrame)
        assert microxs.index.name == 'nuclide'
        assert microxs.columns.values.tolist() == [
            '(n,gamma)', '(n,2n)', '(n,p)', '(n,a)', '(n,3n)', '(n,4n)', 'fission']


    def test_get_spent_comps(self):
        '''
        Test the compositions that are returned from the 
        '''
        spent_comps = self.deplete.get_spent_comps(['5','6','7'])
        assert 10010000 in spent_comps[0].keys()
        assert 922350000 in spent_comps[0].keys()
        assert 932410000 not in spent_comps[0].keys()
        assert spent_comps[0][922350000] == 1.072843157632183e-10

