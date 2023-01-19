from cyclus.agents import Facility 
from cyclus import lib
import cyclus.typesystem as ts

class DepleteReactor(Facility):
    '''
    Reactor facility that performs depletion of the materials
    in it's inventory using the IndependentOperator in 
    OpenMC.
    '''

    fuel_incommods = ts.VectorString(
        doc="Fresh fuel commodity",
        tooltip="Name of commodity requested",
        uilabel="Input Commodity",
        #uitype="incommodity",
    )

    fuel_inrecipes = ts.VectorString(
        doc = "Fresh fuel recipe",
        tooltip = "Fresh fuel recipe",
        uilabel = "Input commodity recipe"
    )

    fuel_outcommods = ts.VectorString(
        doc="Spent fuel commodity",
        tooltip="Name of commodity to bid away",
        uilabel="Output Commodity",
        uitype="outcommodity",
    )

    fuel_outrecipes = ts.VectorString(
        doc = "Spent fuel recipe",
        tooltip = "Spent fuel recipe",
        uilabel = "Output commodity recipe"
    )

    assem_size = ts.Double(
        doc = "Mass (kg) of a single fuel assembly",
        tooltip="Mass (kg) of a single fuel assembly",
        uilabel="Assembly Size",
        #uitype='assemsize',
        units="kg"
    )

    cycle_time = ts.Double(
        doc="Amount of time between requests for new fuel",
        tooltip = "Amount of time between requests for new fuel",
        uilabel="Cycle Time",
        #uitype="cycletime",
        units="months"
    )

    refuel_time = ts.Int(
        doc = "Time steps for refueling",
        tooltip="Time steps for refueling",
        uilabel="refueltime"
    )

    n_assem_core = ts.Int(
        doc = "Number of assemblies in a core",
        tooltip = "Number of assemblies in a core",
        uilabel = "n_assem_core"
    )

    n_assem_batch = ts.Int( 
        doc = "Number of assemblies per batch",
        tooltip = "Number of assemblies per batch",
        uilabel = "n_assem_batch"
    )

    power_cap = ts.Double(
        doc = "Maximum amount of power (MWe) produced",
        tooltip = "Maximum amount of power (MWe) produced",
        uilabel = "power_cap",
        units = "MW"
    )
    
    core = ts.ResBufMaterialInv()
    waste = ts.ResBufMaterialInv()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entry_times = []

    def tick(self):
        t = self.context.time
        finished_cycle = self.context.time - self.cycle_time
        while (not self.core.empty()) and (self.entry_times[0] <= finished_cycle): 
            self.waste.push(self.core.pop_n(self.assem_size))
            del self.entry_times[0]
 
    def tock(self):
        t = self.context.time
        while not self.core.empty():
            self.waste.push(self.core.pop())
            self.entry_times.append(t)  
        if (self.cycle_step >=0) and (self.check_core_full()):
            self.produce_power(True)
        else:
            self.produce_power(False)
        self.batch_gen += 1 

    def enter_notify(self):
        super().enter_notify()
        t = self.context.time
        self.core.capacity = self.assem_size*self.n_assem_core
        self.cycle_step = 0
        self.batch_gen = 0
  
    def check_decommission_condition(self):
        super().check_decommission_condition()

    def get_material_requests(self): # phase 1
        '''
        Send out bid for fuel_incommods
        '''
        port = []
        qty = {}
        mat = {}
        t = self.context.time
        commods = []
        # Initial core laoding (need to fill to capacity)
        if self.batch_gen == 0:
            request_qty = self.core.capacity
        else: 
            request_qty = self.assem_size*self.n_assem_batch
        #for recipes in self.fuel_inrecipes:
        recipe = self.context.get_recipe('uox')
        target = ts.Material.create_untracked(request_qty, recipe)
        commods = {'uox':target}
        port = {"commodities":commods, "constraints":request_qty}
        return port

    def get_material_bids(self, requests): # phase 2
        '''
        Read bids for fuel_outcommods and return bid protfolio
        '''
        bids = []
        reqs = requests['spent_uox']
        recipe_comp = self.context.get_recipe('spent_uox')
        for req in reqs:
            if self.waste.empty():
                break  
            quantity = min(self.waste.quantity, req.target.quantity)
            mat = ts.Material.create_untracked(quantity, recipe_comp)
            bids.append({'request':req, 'offer':mat})
        if len(bids) == 0:
            return 
        port = {"bids": bids}
        return port

    def get_material_trades(self, trades): #phase 5.1
        '''
        Trade away material in the waste material buffer
        '''
        responses = {}
        for trade in trades:
            if trade.request.commodity in self.fuel_outcommods:
                mat_list = self.waste.pop_n(self.waste.count)
        #    if len(mat_list) > 1:
        #    for mat in mat_list[1:]:
        #        mat_list[0].absorb(mat)
            responses[trade] = mat_list[0]
            mat = ts.Material.create(self, trade.amt, trade.request.target.comp())
        #    responses[trade] = mat
        return responses

    def accept_material_trades(self, responses): # phase 5.2
        '''
        Accept bid for fuel_incommods
        '''
        for key, mat in responses.items():
            if key.request.commodity in self.fuel_incommods:
                self.core.push(mat)


    def produce_power(self, produce=True):
        if produce:
            lib.record_time_series(lib.POWER, self, float(self.power_cap))
        else:
            lib.record_time_series(lib.POWER, self, 0)
    
    def check_core_full(self):
        if self.core.count == self.core.capacity:
            return True
        else:
            return False 
