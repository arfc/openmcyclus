import os
import uuid
import sqlite3
import platform

#import tables
import numpy as np
from numpy.testing import assert_array_almost_equal
from numpy.testing import assert_almost_equal
#from cyclus.lib import Env
import unittest

import tests.helper
from tests.helper import check_cmd, run_cyclus, table_exist, cyclus_has_coin

#ALLOW_MILPS = Env().allow_milps
     
class TestDepleteReactor(unittest.TestCase):
    '''
    Test the capabilities of the DepleteReactor in a 
    simulation. 
    ''' 

    def setUp(self):
        self.ext = ".sqlite"

        os.system('rm ' + self.output_file)
        run_cyclus("cyclus", os.getcwd(), self.input_file, self.output_file)
        
        # Get specific tables and columns
        self.conn = sqlite3.connect(self.output_file)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        exc = self.cur.execute
        self.agent_entry = exc('SELECT * FROM AgentEntry').fetchall()
        self.agent_exit = exc('SELECT * FROM AgentExit').fetchall() \
            if len(exc(
                ("SELECT * FROM sqlite_master WHERE "
                 "type='table' AND name='AgentExit'")).fetchall()) > 0 \
                 else None
        self.enrichments = exc('SELECT * FROM Enrichments').fetchall() \
            if len(exc(
                ("SELECT * FROM sqlite_master WHERE "
                 "type='table' AND name='Enrichments'")).fetchall()) > 0 \
                 else None
        self.resources = exc('SELECT * FROM Resources').fetchall()
        self.transactions = exc('SELECT * FROM Transactions').fetchall()
        self.compositions = exc('SELECT * FROM Compositions').fetchall()
        self.info = exc('SELECT * FROM Info').fetchall()
        self.rsrc_qtys = {
            x["ResourceId"]: x["Quantity"] for x in self.resources}
        

    def tearDown(self):
        self.conn.close()

    def find_ids(self, spec, a, spec_col="Spec", id_col="AgentId"):
        if self.ext == '.h5':
            return helper.find_ids(spec, a[spec_col], a[id_col])
        else:
            return [x[id_col] for x in a if x[spec_col] == spec]

    def to_ary(self, a, k):
        if self.ext == '.sqlite':
            return np.array([x[k] for x in a])
        else:
            return a[k]

class TestSimple(TestDepleteReactor):
    '''This class tests the results of a simple simulation. 
    The simulation lasts 10 time steps, 
    the reactor is an initial facility and has an exit time of 
    -1 (doesn't retire during the simulation). The reactor has 3 
    assemblies per core, 1 assembly per batch, 
    cycle time of 3 time steps, refueling time of 1 time step. 
    '''
    def setUp(self):
        self.input_file = "examples/simple.xml"
        self.output_file = "simple_integration.sqlite"
        super(TestSimple, self).setUp()

    def test_agent_entry(self):
        pass  
        tbl = self.agent_entry
        agent_ids = self.to_ary(self.agent_entry, "AgentId")
        enter_time = self.to_ary(self.agent_entry, "EnterTime")
        lifetimes = self.to_ary(self.agent_entry, "Lifetime")
        rx_id = self.find_ids(":openmcyclus.DepleteReactor:DepleteReactor", tbl)
        assert len(agent_ids) == 5
        assert len(rx_id) == 1
        assert all(enter_time == [0, 0, 0, 0, 0])
        assert all(lifetimes == [-1, -1, -1, -1, -1])

    def test_transactions(self):
        tbl = self.transactions
        commodities = self.to_ary(tbl, "Commodity")
        times = self.to_ary(tbl,"Time")
        unique, counts = np.unique(commodities, return_counts=True)
        count_dict = dict(zip(unique,counts))
        assert len(tbl) == 9
        assert count_dict['uox'] == 6
        assert count_dict['spent_uox'] == 3
        assert all(times == [0,0,0,2,2,5,5,8,8])

    def test_resources(self):
        tbl = self.resources
        times = self.to_ary(tbl, "TimeCreated")
        quantities = self.to_ary(tbl, "Quantity")
        assert len(tbl) == 6
        assert all(times == [0,0,0,2,5,8])
        assert all(quantities == [10]*6)

class TestComplex(TestDepleteReactor):
    '''This class tests the results of a more 
    complex simulation. 
    The simulation lasts 20 time steps, 
    the reactor is deployed at time step 3 and has a lifetime 
    of 10 timesteps. The reactor has 3 
    assemblies per core, 1 assembly per batch, 
    cycle time of 3 time steps, refueling time of 1 time step. 
    '''
    def setUp(self):
        self.input_file = "examples/complex.xml"
        self.output_file = "complex_integration.sqlite"
        super(TestComplex, self).setUp()

    def test_agent_entry(self):
        pass  
        tbl = self.agent_entry
        agent_ids = self.to_ary(self.agent_entry, "AgentId")
        enter_time = self.to_ary(self.agent_entry, "EnterTime")
        lifetimes = self.to_ary(self.agent_entry, "Lifetime")
        rx_id = self.find_ids(":openmcyclus.DepleteReactor:DepleteReactor", tbl)
        assert len(agent_ids) == 5
        assert len(rx_id) == 1
        assert all(enter_time == [0, 0, 0, 0, 3])
        assert all(lifetimes == [-1, -1, -1, -1, 10])

    def test_transactions(self):
        tbl = self.transactions
        commodities = self.to_ary(tbl, "Commodity")
        times = self.to_ary(tbl,"Time")
        unique, counts = np.unique(commodities, return_counts=True)
        count_dict = dict(zip(unique,counts))
        assert len(tbl) == 9
        assert count_dict['uox'] == 6
        assert count_dict['spent_uox'] == 3
        assert all(times == [3,3,3,5,5,8,8,11,11])

    def test_resources(self):
        tbl = self.resources
        times = self.to_ary(tbl, "TimeCreated")
        quantities = self.to_ary(tbl, "Quantity")
        assert len(tbl) == 6
        assert all(times == [3,3,3,5,8,11])
        assert all(quantities == [10]*6)
