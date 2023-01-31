import numpy as np
import pytest 
from openmcyclus.depletion import OpenMCDepletion
import xml.etree.ElementTree as ET
import unittest

class TestOpenMCDepletion(unittest.TestCase):
    def setUp(self):
        '''
        Set up the instantiation of the OpenMCDeplete class
        '''
        self.deplete = OpenMCDepletion("../", 'Reactor', "chain_endfb71_pwr.xml", 10, 100)

    def test_read_model(self):
        '''
        Test for when the files are found
        '''
        model = self.deplete.read_model()
        assert 2 == 2

    def test_read_microxs(self):
        microxs = self.deplete.read_microxs()
        assert 2 == 2

    def test_create_recipe(self):
        self.deplete.create_recipe()
        output_recipe = "../Reactor_fuel.xml"
        tree = ET.parse(output_recipe)
        root = tree.getroot()
        assert root.tag == 'recipes'
        assert root[0].tag == 'recipe'
        assert root[0][0].tag == 'name'
        assert root[0][1].tag == 'basis'
        assert root[0][2].tag == 'nuclide'
        assert root[0][2][0].tag == 'id'
        assert root[0][2][1].tag == 'comp'
    
