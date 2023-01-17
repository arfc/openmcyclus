from cyclus.agents import Facility 
import cyclus.typesystem as ts

class DepleteReactor(Facility):
    '''
    Reactor facility that performs depletion of the materials
    in it's inventory using the IndependentOperator in 
    OpenMC.
    '''

    fuel_incommods = ts.String(
        doc="Fresh fuel commodity",
        tooltip="Name of commodity requested",
        uilabel="Input Commodity",
        #uitype="incommodity",
        #alias = ['fuel_incommods']
    )

    fuel_inrecipes = ts.String(
        doc = "Fresh fuel recipe",
        tooltip = "Fresh fuel recipe",
        uilabel = "Input commodity recipe"
    )

    fuel_outcommods = ts.String(
        doc="Spent fuel commodity",
        tooltip="Name of commodity to bid away",
        uilabel="Output Commodity",
        uitype="outcommodity",
    )

    fuel_outrecipes = ts.String(
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
    
    def __init__(self, ctx):
        super().__init__(ctx)

    def enter_notify(self):
        super().enter_notify()

    def check_decommission_condition(self):
        super().check_decommission_condition()

    def get_material_requests(self):
        super().get_material_requests()

    def get_material_trades(self, trades):
        super().get_material_trades(trades)

    def get_material_bids(self, requests):
        super().get_material_bids(requests)

    def accept_material_trades(self, responses):
        super().accept_material_trades(responses)

    def get_product_trades(self, trades):
        super().get_product_trades(trades)

    def get_product_bids(self, requests):
        super().get_product_bids(requests)

    def get_product_requests(self):
        super().get_product_requests()

    def accept_product_trades(self, trades):
        super().accept_product_trades(trades)

    def decision(self):
        super().decision()

    def tick():
        print("Iteration 1")