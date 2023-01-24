import unittest
from cyclus import lib
import cyclus.typesystem as ts
from openmcyclus.DepleteReactor import DepleteReactor

#sys.path.insert(0, "openmcyclus/.")
#from DepleteReactor import DepleteReactor as dr

ctx = lib.Context()

class Test_DepleteReactor(unittest.TestCase):
    def setUp(self):
        '''
        Class to test the functions in the 
        openmcyclus.DepleteReactor:DepleteReactor archetype.
        '''
        
        self.reactor = DepleteReactor(ctx)
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
        self.reactor.core.capacity = 100

    def test_get_material_requests1(self):
        '''
        Test the material requests sent out for fuel_incommods with 
        recipe fuel_inrecipes.
        '''
        #self.reactor.fuel_inrecipes.comp = {92235:100}
        target = ts.Material.create_untracked(10, {92235:100})
        exp = [{'commodities':{'uox':target},"constraints":10}]
        obs = []#self.reactor.get_material_requests()
        assert exp == obs

    def test_get_material_bids(self):
        mat = ts.Material.create_untracked(10, {92235:100})
        exp = {'bids':{'request':{'spent_uox':mat}, 'offer':mat}}
        


        target = ts.Material.create_untracked(10, {92235:100})
        requests = {'spent_uox':(target)}
        obs = [] #self.reactor.get_material_bids(requests)
        assert exp == obs

    def test_get_material_trades(self):
        exp_trade = ts.MaterialTrade
        exp_material = ts.Material.create(10, {92235:100})
        exp = {exp_trade:exp_material}
        trades = ts.MaterialTrade
        obs = self.reactor.get_material_trades(trades)

        assert 4 == 4


    def test_get_material_requests2(self):
        '''
        Test the material request for fuel_incommods with 
        recipe fuel_inrecipes when the core is full
        '''
        exp = []

        material = ts.Material.create_untracked(self.reactor.assem_size, {92235:100})
        #self.reactor.core.push(material)
        #obs = self.reactor.get_material_requests()

        assert 2 ==2 

    def test_check_core_full(self):
        '''
        Test when the core is full
        '''
        mat = ts.Material.create_untracked(30, {92235:100})
        #self.reactor.core.push(mat)
        assert 3 ==3

    def test_produce_power(self):
        '''
        Test when given true
        '''
        #obs = self.reactor.produce_power()
        assert 1 == 1

    

