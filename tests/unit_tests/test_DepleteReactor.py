import numpy as np
import unittest
from cyclus import lib
import cyclus.typesystem as ts
import sys
import pytest
from openmcyclus import DepleteReactor as dr

#sys.path.insert(0, "openmcyclus/.")
#from DepleteReactor import DepleteReactor as dr


class Test_DepleteReactor(unittest.TestCase):
    def setup(self):
        '''
        Class to test the functions in the 
        openmcyclus.DepleteReactor:DepleteReactor archetype.
        '''
        self.fuel_incommods = ['uox']
        self.out_commods = ['spent_uox']
        self.fuel_inrecipes = ['uox']
        self.fuel_outrecipes = ['spent_uox']
        self.assem_size = 10
        self.cycle_time = 3
        self.refuel_time = 1
        self.n_assem_core = 3
        self.n_assem_batch = 1
        self.power_cap = 100
        self.fresh_fuel = ts.ResBufMaterialInv()
        self.core = ts.ResBufMaterialInv()
        self.spent_fuel = ts.ResBufMaterialInv()

    def test_check_core_full(self):
        '''
        Test when the core is full
        '''
        self.core.quantity = 30
        assert dr.check_core_full() == True

        