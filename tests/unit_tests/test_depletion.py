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
            "chain_endfb71_pwr.xml", 10, 100e-6)

    def test_read_materials(self):
        '''
        Test when the material file is found
        '''
        materials = self.deplete.read_materials("examples/")
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
        mats = openmc.Materials.from_xml("examples/materials.xml")
        material_ids, materials = self.deplete.update_materials(comps, mats)
        assert materials[0].nuclides == [openmc.material.NuclideTuple('U235',0.05, 'wo'), 
                                         openmc.material.NuclideTuple('U238',0.95, 'wo')]
        assert materials[1].nuclides == [openmc.material.NuclideTuple('Cs137',0.1, 'wo'),
                                         openmc.material.NuclideTuple('Kr85',0.80, 'wo'),
                                         openmc.material.NuclideTuple('Xe135',0.10, 'wo')]
        assert materials[2].nuclides == [openmc.material.NuclideTuple('Pu239',0.10, 'wo'), 
                                         openmc.material.NuclideTuple('Pu241',0.90, 'wo')]
        assert material_ids == [5,6,7]

    def test_read_microxs(self):
        microxs = self.deplete.read_microxs("examples/")
        assert isinstance(microxs, pd.DataFrame)
        assert microxs.index.name == 'nuclide'
        assert microxs.columns.values.tolist() == [
            '(n,gamma)', '(n,2n)', '(n,p)', '(n,a)', '(n,3n)', '(n,4n)', 'fission']


    def test_get_spent_comps(self):
        '''
        Test the compositions that are returned from running depletion. 
        First, the materials are defined and then depletion is run to prevent 
        having to store an HDF5 database in the repo
        '''
        comps = [{922350000:0.04, 922380000:0.96}, 
                 {551370000:0.1, 360850000:0.8, 541350000:0.1}, 
                 {942390000:0.10, 942410000:0.9}]
        self.deplete.run_depletion("examples/", comps)
        spent_comps = self.deplete.get_spent_comps(['5','6','7'], "examples/")
        assert 551370000 in spent_comps[0].keys()
        assert 922350000 in spent_comps[0].keys()
        assert 932410000 not in spent_comps[0].keys()
        assert spent_comps[0][922350000] == 0.039999352943069735

