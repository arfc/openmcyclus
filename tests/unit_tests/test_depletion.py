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
            "tests/", 'Reactor', "chain_endfb71_pwr.xml", 10, 100)

    def test_read_model(self):
        '''
        Test for when the files are found
        '''
        model = self.deplete.read_model()
        assert isinstance(model, openmc.model.model.Model)

    def test_read_microxs(self):
        microxs = self.deplete.read_microxs()
        assert isinstance(microxs, pd.DataFrame)
        assert microxs.index.name == 'nuclide'
        assert microxs.columns.values.tolist() == [
            '(n,gamma)', '(n,2n)', '(n,p)', '(n,a)', '(n,3n)', '(n,4n)', 'fission']

    def test_run_depletion(self):
        self.deplete.run_depletion()
        assert (self.deplete.path / "depletion_results.h5").exists()

    def test_create_recipe(self):
        self.deplete.run_depletion()  # make sure database is present
        self.deplete.create_recipe()
        (self.deplete.path / "depletion_results.h5").unlink()
        output_recipe = "tests/Reactor_fuel.xml"
        tree = ET.parse(output_recipe)
        root = tree.getroot()
        assert root.tag == 'recipes'
        assert root[0].tag == 'recipe'
        assert root[0][0].tag == 'name'
        assert root[0][1].tag == 'basis'
        assert root[0][2].tag == 'nuclide'
        assert root[0][2][0].tag == 'id'
        assert root[0][2][1].tag == 'comp'
