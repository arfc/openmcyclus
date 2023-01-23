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
        units="kg",
        default= 0
    )

    cycle_time = ts.Double(
        doc="Amount of time between requests for new fuel",
        tooltip = "Amount of time between requests for new fuel",
        uilabel="Cycle Time",
        #uitype="cycletime",
        units="months",
        default=0
    )

    refuel_time = ts.Int(
        doc = "Time steps for refueling",
        tooltip="Time steps for refueling",
        uilabel="refueltime",
        default = 0
    )

    n_assem_core = ts.Int(
        doc = "Number of assemblies in a core",
        tooltip = "Number of assemblies in a core",
        uilabel = "n_assem_core",
        default=0
    )

    n_assem_batch = ts.Int( 
        doc = "Number of assemblies per batch",
        tooltip = "Number of assemblies per batch",
        uilabel = "n_assem_batch",
        default=0
    )

    power_cap = ts.Double(
        doc = "Maximum amount of power (MWe) produced",
        tooltip = "Maximum amount of power (MWe) produced",
        uilabel = "power_cap",
        units = "MW",
        default=0
    )
   
    fresh_fuel = ts.ResBufMaterialInv()
    core = ts.ResBufMaterialInv()
    spent_fuel = ts.ResBufMaterialInv()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fresh_fuel_entry_times = []
        self.core_entry_times = []
        self.fresh_fuel.capacity = self.assem_size*self.n_assem_core
        self.core.capacity = self.assem_size*self.n_assem_core

    def tick(self):
        print("tick ", self.context.time, self.fuel_inrecipes[0])
        finished_cycle = self.context.time - self.cycle_time
        while (not self.core.empty()) and (self.fresh_fuel_entry_times[0] <= finished_cycle): 
            self.spent_fuel.push(self.core.pop(self.assem_size))
            del self.core_entry_times[0] 
 
    def tock(self):
        time_diff = self.context.time - self.fresh_fuel_entry_times[0]
        if (not self.fresh_fuel.empty()) and (time_diff > self.refuel_time):
            self.core.push(self.fresh_fuel.pop(self.assem_size))
            del self.fresh_fuel_entry_times[0]
            self.core_entry_times.append(self.context.time)
        print("tock ", self.context.time, self.core.quantity)
        if (self.check_core_full()):
            self.produce_power(True)
        else:
            self.produce_power(False)

    def enter_notify(self):
        super().enter_notify()        
  
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
        if self.check_core_full():
            return port
        request_qty = self.assem_size
        for recipes in self.fuel_inrecipes:
            recipe = self.context.get_recipe(recipes)
            target = ts.Material.create_untracked(request_qty, recipe)
            for commod in self.fuel_incommods:
                commods = {commod:target}
                port.append({"commodities":commods, "constraints":request_qty})
        return port

    def get_material_bids(self, requests): # phase 2
        '''
        Read bids for fuel_outcommods and return bid protfolio
        '''
        bids = []
        reqs = requests['spent_uox']
        recipe_comp = self.context.get_recipe('spent_uox')
        for req in reqs:
            if self.spent_fuel.empty():
                break  
            quantity = min(self.spent_fuel.quantity, req.target.quantity)
            mat = ts.Material.create_untracked(quantity, recipe_comp)
            bids.append({'request':req, 'offer':mat})
        if len(bids) == 0:
            return 
        port = {"bids": bids}
        return port

    def get_material_trades(self, trades): #phase 5.1
        '''
        Trade away material in the spent_fuel material buffer
        '''
        responses = {}
        for trade in trades:
            if trade.request.commodity in self.fuel_outcommods:
                mat_list = self.spent_fuel.pop(self.assem_size)
                #print(mat_list[0])
        #    if len(mat_list) > 1:
        #    for mat in mat_list[1:]:
        #        mat_list[0].absorb(mat)
            responses[trade] = mat_list[0]
        #    mat = ts.Material.create(self, trade.amt, trade.request.target.comp())
        #    responses[trade] = mat
        return responses

    def accept_material_trades(self, responses): # phase 5.2
        '''
        Accept bid for fuel_incommods
        '''
        for key, mat in responses.items():
            if key.request.commodity in self.fuel_incommods:
                self.fresh_fuel.push(mat)
                self.fresh_fuel_entry_times.append(self.context.time)


    def produce_power(self, produce=True):
        '''
        If true, then record the power_cap value in the 
        lib.POWER time series. If not, then record 0. 
        '''
        if produce:
            lib.record_time_series(lib.POWER, self, float(self.power_cap))
        else:
            lib.record_time_series(lib.POWER, self, 0)
    
    def check_core_full(self):
        '''
        Check if the core has the total amount of 
        material as the core capacity
        '''
        if self.core.quantity == self.core.capacity:
            return True
        else:
            return False 
