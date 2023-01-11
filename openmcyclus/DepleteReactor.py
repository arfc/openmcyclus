from cyclus.agents import Facility 
#from cyclus import lib
#import cyclus.typesystem as ts

class DepleteReactor(Facility):
    '''
    Reactor facility that performs depletion of the materials
    in it's inventory using the IndependentOperator in 
    OpenMC.
    '''

    #def __init__(self, ctx):
    #    super().__init__(ctx)
    #    self.entry_times = []

    fuel_incommods = ts.String(
        doc="Fresh fuel commodity",
        tooltip="Name of commodity requested",
        uilabel="Input Commodity",
        uitype="incommodity",
    )

    fuel_outcommods = ts.String(
        doc="Spent fuel commodity",
        tooltip="Name of commodity to bid away",
        uilabel="Output Commodity",
        uitype="outcommodity",
    )

    assem_size = ts.Double(
        doc = "Size of a single fuel assembly",
        tooltip="Size of a single fuel assembly",
        uilabel="Assembly Size",
        uityle='assemsize',
        default=1,
        units="kg"
    )

    cycle_time = ts.Double(
        doc="Amount of time between requests for new fuel",
        tooltip = "Amount of time between requests for new fuel",
        uilabel="Cycle Time",
        uitype="cycletime",
        units="months"
    )


    def tick(self):
        print("Hello World!")
