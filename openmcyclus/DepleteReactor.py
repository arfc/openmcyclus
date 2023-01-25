from cyclus.agents import Facility 
from cyclus import lib
import cyclus.typesystem as ts
import math

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

    n_assem_fresh = ts.Int(
        doc = "Number of fresh fuel assemblies to keep on hand "\
              "if possible",
        default = 0,
        range = [0,3],
        uilabel="Minimum fresh fuel inventory",
        units = "assemblies"
    )

    n_assem_spent = ts.Int(
        doc = "Number of spent fuel assemblies that can be stored "\
              "on-site before reactor operation stalls",
        default = 10000000,
        uilabel="Maximum spent fuel inventory",
        units = "assemblies"
    )

    power_cap = ts.Double(
        doc = "Maximum amount of power (MWe) produced",
        tooltip = "Maximum amount of power (MWe) produced",
        uilabel = "power_cap",
        units = "MW",
        default=0
    )

    decom_transmute_all = ts.String(
        doc = "If true, the archetype transmutes all assemblies "\
              "upon decommisioning. If false, the archetype only "\
              "transmutes half.",
        default = False
    )
   
    fresh_fuel = ts.ResBufMaterialInv()
    core = ts.ResBufMaterialInv()
    spent_fuel = ts.ResBufMaterialInv()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fresh_fuel_entry_times = []
        self.core_entry_times = []
        self.fresh_fuel.capacity = self.assem_size*self.n_assem_fresh
        self.core.capacity = self.assem_size*self.n_assem_core
        self.spent_fuel.capacity = self.assem_size*self.n_assem_spent
        self.cycle_steps = 0
        self.power_name = "power"
        self.discharged = True
        self.ctx = lib.Context()

    def tick(self):
        '''
        Logic to implement at the tick phase of each 
        time step. 
        
        If the prototype is retired, then that is recorded, 
        fuel is transmuted, and the prototype is decommissioned. 

        If it's the end of a cycle, that is recorded. If it is 
        after a cycle ends, and fuel has not been discharged, 
        then the fuel is discharged. If it's after a cycle ends, then 
        fuel is loaded
        '''

        if self.retired():
            self.record("RETIRED", "")

            if self.context.time == self.exit_time + 1:
                if self.decom_transmute_all == True:
                    self.transmute(math.ceil(self.n_assem_core))
                else:
                    self.transmute(math.ceil(self.n_assem_core/2))

            while self.core.count > 0:
                if self.discharge() == False:
                    break

            while (self.fresh_fuel > 0) and (self.spent_fuel.space >= self.assem_size):
                self.spent_fuel.push(self.fresh_fuel.pop())
            if self.check_decommission_condition():
                self.decommission()

        if self.cycle_step == self.cycle_time:
            self.transmute()
            self.record("CYCLE_END", "")
        if (self.cycle_step >= self.cycle_time) and (self.discharged not False):
            self.discharged = self.discharge()
        if self.cycle_step >= self.cycle_time:
            self.load()
 
    def tock(self):
        '''
        Logic to implement at the tock phase of each 
        time step. 

        If the prototype is retired, then nothing happens. 

        If it's after a cycle ends and the refueling time has passed,
        the core is full, and fuel has been discharged, then 
        the discharged variable is changed to false and the 
        cycle length counter is restarted.

        If it's the beginning of a new cycle and the core is full, 
        then a cycle start is recorded. 

        If it's in the middle of a cycle and the core is full, the 
        the power_cap value is recorded as power generated. If these 
        conditions aren't met, then a power of 0 is recorded. 

        If it's in the middle of a cycle or the core is full, then 
        the cycle duration counter increases by one. 
        '''
        if self.retired():
            return
        if (self.cycle_step >= self.cycle_time+self.refuel_time) and (self.core.count == self.n_assem) and (self.discharged == True):
            self.discharged = False
            self.cycle_step = 0
        if (self.cycle_step == 0) and (self.core.count == self.n_assem_core):
            self.record("CYCLE_START", "")
        if (self.cycle_step >=0) and (self.cycle_sept < self.cycle_time) and (self.core.count == self.n_assem_core):
            self.produce_power(True)
        else:
            self.produce_power(False)  

        if (self.cycle_step > 0) or (self.core.count == self.n_assem_core):
            self.cycle_step += 1  


        time_diff = self.context.time - self.fresh_fuel_entry_times[0]
        if (not self.fresh_fuel.empty()) and (time_diff > self.refuel_time):
            self.core.push(self.fresh_fuel.pop(self.assem_size))
            del self.fresh_fuel_entry_times[0]
            self.core_entry_times.append(self.context.time)
        #print("tock ", self.context.time, self.core.quantity)

    def enter_notify(self):
        super().enter_notify()       
  
    def check_decommission_condition(self):
        '''
        If the core and the spent fuel are empty, then the core can be 
        decommissioned.
        '''
        if (self.core.count == 0) and (self.spent_fuel.count == 0):
            return True
        else:
            return False

    def get_material_requests(self): # phase 1
        '''
        Send out bid for fuel_incommods. 

        The number of assemblies to order is the total number needed 
        for the core less what is currently in the core plus 
        how many need to be in the fresh fuel storage less how many 
        exist there already. 

        If the reactor has a finite lifetime, calculate the number of 
        cycles left and the number of assemblies needed for the 
        lifetime of the reactor. Order whichever number is 
        lower. 
        
        If the reactor does not need more fuel or is retired, then 
        submit no bids for materials.
        '''
        port = []
        n_assem_order = self.n_assem_core - self.core.count + self.n_assem_fresh + self.fresh_fuel.count
        if self.exit_time != -1:
            time_left = self.exit_time - self.context.time + 1
            time_left_cycle = self.cycle_time + self.refuel_time - self.cycle_step
            n_cycles_left = (time_left - time_left_cycle)/(self.cycle_time + self.refuel_time)
            n_cycles_left = math.ceil(n_cycles_left)
            n_need = max(0, n_cycles_left*self.n_assem_batch - self.n_assem_fresh + self.assem_core - self.core.count)
            n_assem_order = min(n_assem_order, n_need)

        if n_assem_order == 0:
            return port
        elif self.retired():
            return port
        for ii in range(n_assem_order):
            for jj in range(len(self.fuel_incommods)):
                commod = self.fuel_incommods[jj]
                recipe = self.context.get_recipe(self.fuel_inrecipes[jj])
                material = ts.Material.create_untracked(self.assem_size, recipe)
        lib.record_time_series("demand"+commod, self, self.assem_size*n_assem_order)
        port.append({"commodities":commod, "constraints":self.assem_size*n_assem_order})
        return port

    def get_material_bids(self, requests): # phase 2
        '''
        Read bids for fuel_outcommods and return bid protfolio
        '''
        got_mats = False
        bids = []
        if unique_commods_.empty():
            for ii in range(len(self.fuel_outcommods)):
                unique_commods_.insert(self.fuel_commods[ii])

        for ii in [unique_commods_.begin, unique_commods_.end]:
            reqs = requests[commod]
            if len(reqs) == 0:
                continue
            elif (!gotmats):
                all_mats = PeekSpent()

            mats = all_mats[commod]
            if len(mats) == 0:
                continue
            for jj in range(len(reqs)):
                req = reqs[jj]
                tot_bid = 0
                for kk in range(len(mats)):
                    m = mats[k]
                    tot_bid += m.quantity
                    bid.append({'request':req,'offer':m})
                    if tot_bid >= req.target.quantity:
                        break
            tot_qty = 0
            for jj in range(len(mats)):
                tot_qty += mats[jj].quantity

        port = {'bids':bids}
        return port

    def get_material_trades(self, trades): #phase 5.1
        '''
        Trade away material in the spent_fuel material buffer
        '''
        responses = {}
        for ii in range(len(trades)):
            commod = trades[ii].request.commodity
            m = mats[commod].back
            mat[commod].pop_back()
            responses.append(trades[ii], m)
            res_indexes.erase(m.obj_id())
        self.push_spent(mats)
        return responses

    def accept_material_trades(self, responses): # phase 5.2
        '''
        Accept bid for fuel_incommods
        '''
        #ss = stringstream 
        n_load = min(len(responses), self.n_assem_core - self.core.count)
        if n_load > 0:
            ss == str(n_load) + " assemblies"
            self.record("LOAD", ss)

        for trade = responses.begin(); trade != responses.end(); ++ trade:
            commod = trade.request.commodity
            m = trade.second
            if self.core.count < self.n_assem_core:
                self.core.push(m)
            else:
                self.fresh_fuel.push(m)


    def produce_power(self, produce=True):
        '''
        If true, then record the power_cap value in the 
        lib.POWER time series. If not, then record 0. 
        '''
        if produce:
            lib.record_time_series(lib.POWER, self, float(self.power_cap))
            lib.record_time_series("supplyPOWER", self, float(self.power_cap))
        else:
            lib.record_time_series(lib.POWER, self, 0)
            lib.record_time_series("supplyPOWER", self, 0)
    
    def check_core_full(self):
        '''
        Check if the core has the total amount of 
        material as the core capacity
        '''
        if self.core.quantity == self.core.capacity:
            return True
        else:
            return False 

    def retired(self):
        '''
        Determine if the prototype is retired
        '''
        if (self.exit_time != -1) and (self.context.time > self.exit_time):
            return True
        else:
            return False

    def discharge(self):
        '''
        '''
        npop = min(self.assem_batch, self.core.count)
        if (self.n_assem_spent - self.spent_fuel.count) < npop:
            self.record("DISCHARGE", "failed")
            return False
        #ss = stringstream 
        ss = str(npop) + " assemblies"
        self.record("DISCHARGE", ss)
        self.spent_fuel.push(self.core.pop_n(npop))

        for ii in range(len(self.fuel_outcommods)):
            spent_mats = self.spent_fuel.peek()
            mats = spent_mats[self.fuel_outcommods[ii]]
            tot_spent = 0
            for jj in range(len(mats)):
                m = mats[jj]
                tot_spent += m.quantity
        return True

    def load(self):
        '''
        '''
        n = min(self.n_assem_core-self.core.count, self.fresh_fuel.count)
        if n == 0:
            return
        #ss = stringstream 
        ss = str(n) + " assemblies"
        self.record("LOAD", ss)
        self.core.push(self.fresh_fuel.pop_n(n))


    def transmute(self):
        '''
        '''

    def record(self, event, val):
        '''
        Record a reactor event to the output database with the 
        given name and note val

        Parameters:
        -----------
        event: str 
            name of event
        val: str
            value of event
        '''
        lib.Datum.add_val("AgentId", id())
        lib.Datum.add_val("Time", self.context.time)
        lib.Datum.add_val("Event", event)
        lib.Datum.add_val("Value", val)
        lib.Datum.record()
        return

        
    def index_res(self, incommod):
        for ii in range(len(self.fuel_incommods)):
            if fuel_incommods[ii] == incommod
                res_index[m->obj_id()] = ii 
                return
        raise ValueError 
            "openmcyclus.DepleteReactor:DepleteReactor received "\
                "unsupported incommod material"

    def pop_spent(self):
        '''
        Amount of fuel to trade away from self.spent_fuel
        '''
        mats = self.spent.pop_n(self.spent_fuel.count)
        mapped = []
        for ii in range(len(mats)):
            commod = self.fuel_outcommods(mts[ii])
            mapped[commod].append(mats[i])
        
        for it in [mapped.begin, mapped.end]:
            reverse(it.second.begin(), it.second.end())
        return mapped

    def push_spent(self, leftover):
        for it in [leftover.begin, leftover.end]:
            reverse(it.second.begin, it.second.end)
        self.spent_fuel.push(it.second)