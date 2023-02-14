import os
import uuid
import sqlite3
import platform

import tables
import numpy as np
from numpy.testing import assert_array_almost_equal
from numpy.testing import assert_almost_equal
from cyclus.lib import Env
import unittest

from nose.plugins.skip import SkipTest
from nose.tools import assert_equal, assert_true

import tests.helper
from tests.helper import check_cmd, run_cyclus, table_exist, cyclus_has_coin

#ALLOW_MILPS = Env().allow_milps
     
class TestDepleteReactor(unittest.TestCase):
    '''
    Test the capabilities of the DepleteReactor in a 
    simulation. The simulation lasts 10 time steps, 
    the reactor is an initial facility and has an exit time of 
    -1. The reactor has 3 assemblies per core, 1 assembly per batch, 
    cycle time of 3 time steps, refueling time of 1 time step. 
    ''' 

    def setUp(self):
        self.ext = ".sqlite"
        self.output_file = "integration_tests.sqlite"
        self.input_file = "examples/simple.xml"

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

    def test_agent_entry(self):
        pass  
        tbl = self.agent_entry
        agent_ids = self.to_ary(self.agent_entry, "AgentId")
        enter_time = self.to_ary(self.agent_entry, "EnterTime")
        rx_id = self.find_ids(":openmcyclus.DepleteReactor:DepleteReactor", tbl)
        assert_equal(len(agent_ids), 5)
        #assert_equal(enter_time , 0)