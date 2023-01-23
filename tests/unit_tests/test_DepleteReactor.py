import numpy as np
import unittest
from cyclus import lib
import cyclus.typesystem as ts
import sys
import pytest
from openmcyclus.DepleteReactor import DepleteReactor

#sys.path.insert(0, "openmcyclus/.")
#from DepleteReactor import DepleteReactor as dr


class Test_DepleteReactor(unittest.TestCase):
    def setUp(self):
        '''
        Class to test the functions in the 
        openmcyclus.DepleteReactor:DepleteReactor archetype.
        '''
        self.reactor = DepleteReactor(lib.Context())
        self.reactor.fuel_incommods = ['uox']
        self.reactor.out_commods = ['spent_uox']
        self.reactor.fuel_inrecipes = ['uox']
        self.reactor.fuel_outrecipes = ['spent_uox']
        self.reactor.assem_size = 10
        self.reactor.cycle_time = 3
        self.reactor.refuel_time = 1
        self.reactor.n_assem_core = 3
        self.reactor.n_assem_batch = 1
        self.reactor.power_cap = 100

    def test_get_material_requests(self):
        '''
        
        '''
        exp = [{'commodities':{'uox':'target'},"constraints":10}]
        obs = self.reactor.get_material_requests(self)
        assert exp == obs

    def test_check_core_full(self):
        '''
        Test when the core is full
        '''
        self.reactor.core.push(30)
        assert dr.check_core_full() == True

    

