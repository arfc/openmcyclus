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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tick(self):
        return

    def enter_notify(self):
        super().enter_notify()

    def check_decommission_condition(self):
        super().check_decommission_condition()

    def get_material_requests(self):
        request_qty = self.assem_size
        recipe = self.context.get_recipe('uox')
        target = ts.Material.create_untracked(request_qty, recipe)
        commods = {'uox':target}
        port = {"commodities":commods, "constraints":request_qty}
        return port

    def get_material_bids(self, requests):
        reqs = requests["spent_uox"]
        bids = [req for req in reqs]
        port = {"bids": bids}
        return port

    def get_material_trades(self, trades):
        responses = {}
        for trade in trades:
            mat = ts.Material.create(self, trade.amt, trade.request.target.comp())
            responses[trade] = mat
        return responses

    def accept_material_trades(self, responses):
        for key, mat in responses.items():
            if key.request.commodity in self.fuel_incommods:
                self.core.push(mat)


    def produce_power(self, produce=True):
        if produce:
            lib.record_time_series(lib.POWER, self, float(self.power_cap))
        else:
            lib.record_time_series(lib.POWER, self, 0)
        