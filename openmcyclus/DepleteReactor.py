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
        default = 10000000, #default of None? would need more logic to 
        # account for different data types
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
        self.cycle_step = 0
        self.power_name = "power"
        self.discharged = True
        self.resource_indexes = {}

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
        print("tick", self.context.time, "cycle_step:", self.cycle_step)
        if self.retired():
        #    self.record("RETIRED", "")
            print("retired")
            if self.context.time == self.exit_time + 1:
                if self.decom_transmute_all == True:
                    self.transmute(math.ceil(self.n_assem_core))
                else:
                    self.transmute(math.ceil(self.n_assem_core/2))

            while self.core.count > 0:
                if self.discharge() == False:
                    # Add string to print to terminal to see if this 
                    # gets triggered as expected
                    break

            while (self.fresh_fuel > 0) and (self.spent_fuel.space >= self.assem_size):
                self.spent_fuel.push(self.fresh_fuel.pop())
            if self.check_decommission_condition():
                self.decommission()
        if self.cycle_step == self.cycle_time:  
            print("Transmute fuel")          
            #print("core inventory before transmuting:", self.core.count)
            self.transmute(math.ceil(self.n_assem_batch))
            
            #self.record("CYCLE_END", "")
        
        if (self.cycle_step >= self.cycle_time) and (self.discharged != False):
            print("Discharge fuel")
            self.discharged = self.discharge()
        if self.cycle_step >= self.cycle_time:
            print("Load fuel")
            self.load()
        #self.record("Tick", "")
        print("end tick", self.context.time)
        #lib.Logger('5', str("DepleteReactor" + str(self.power_cap) + "is ticking"))

 
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
        print("begin tock", self.context.time)
        if self.retired():
            print("Retired")
            return
        
        if (self.cycle_step >= self.cycle_time+self.refuel_time) and (self.core.count == self.n_assem) and (self.discharged == True):
            self.discharged = False
            print(self.context.time, "reset cycle_step")
            self.cycle_step = 0
        
        if (self.cycle_step == 0) and (self.core.count == self.n_assem_core):
            #self.record("CYCLE_START", "")
            print("Cycle start")
        if (self.cycle_step >=0) and (self.cycle_step < self.cycle_time) and (self.core.count == self.n_assem_core):
            lib.record_time_series(lib.POWER, self, self.power_cap)
            lib.record_time_series("supplyPOWER", self, self.power_cap)
            print('record power', self.power_cap)
        else:
            lib.record_time_series(lib.POWER, self, 0)
            lib.record_time_series("supplyPOWER", self, 0)  
            print('record power 0')

        if (self.cycle_step > 0) or (self.core.count == self.n_assem_core):
            self.cycle_step += 1  
        print("end tock", self.context.time, "cycle_step:", self.cycle_step)

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
        print("start get requests", self.context.time)
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
            print("nothing to order")
            return port
        elif self.retired():
            print("facility is retired")
            return port
        for ii in range(n_assem_order):
            for commod in self.fuel_incommods:
                recipe = self.context.get_recipe(commod)
                material = ts.Material.create_untracked(self.assem_size, recipe)
            lib.record_time_series("demand"+commod, self, self.assem_size)
            port.append({"commodities":{commod:material}, "constraints":self.assem_size})
        print("end get material requests", self.context.time, port)
        return port

    def get_material_bids(self, requests): # phase 2
        '''
        Read bids for fuel_outcommods and return bid portfolio.

        If the unique_commods_ string is empty, add the names of 
        the fuel out commodities.

        For each of the items in the unique commodities list, 
        if there are no requests for a given commodity name, then 
        continue to the next commodity. Get the recipe for 
        each commodity requested.

        Looking at the composition for each commodity, 
        if there is no composition, then move to the next commodity. 

        For each request of each commodity, sum the total request 
        for the commodity. Then create a bid for each request of 
        each commodity.

        For each material composition sum to total mass of 
        the composition.

        Add a constraint of the total quantity of the commodity available.
        Create a bid portfolio for each request that can be met. 
        '''
        print("start get Material bids")
        #got_mats = False
        bids = []
        #for commod in self.fuel_outcommods:
        #    reqs = requests[commod]
        #    if len(reqs) == 0:
        #        continue
        #    elif (got_mats == False):
        #        all_mats = self.peek_spent()

        #    if len(all_mats) == 0:
        #        tot_qty = 0
        #        continue
        #    mats = [all_mats[commod]]
        #    if len(mats) == 0:
        #        continue
        #    for ii in range(len(self.fuel_outrecipes)):
        #        recipe_comp = self.context.get_recipe(self.fuel_outrecipes[ii])
        #        for req in reqs:
        #            tot_bid = 0
        #            for jj in range(len(mats)):
        #                tot_bid += mats[jj].quantity
        #                qty = min(req.target.quantity, self.spent_fuel.quantity)
        #                mat = ts.Material.create_untracked(qty, recipe_comp)
        #                bids.append({'request':req,'offer':mat})
        #            if tot_bid >= req.target.quantity:
        #                break
        #    tot_qty = 0
        #    for mat in mats:
        #        tot_qty += mat.quantity
        for commod in self.fuel_outcommods:
            if commod in requests.keys():
                reqs = requests[commod]
                for req in reqs:
                    if self.spent_fuel.empty():
                        break
                    qty = min(req.target.quantity, self.spent_fuel.quantity)
                    next_fuel = self.spent_fuel.peek()
                    mat = ts.Material.create_untracked(qty, next_fuel.comp())
                    bids.append({'request':req, 'offer':mat})
        if len(bids) == 0:
            print("no responses to requests", self.context.time)
            return 

        port = {'bids':bids}
        print("end get material bids", self.context.time, port)
        return port

    def get_material_trades(self, trades): #phase 5.1
        '''
        Trade away material in the spent_fuel material buffer.

        Pull out the material from spent fuel inventory
        For each trade, get the commodity name, get the 
        composition of the trade.

        Then trade the materials from the spent fuel inventory. 
        '''
        print("start get material trades")
        responses = {}
        mats = self.pop_spent()
        for ii in range(len(trades)):
            commod = trades[ii].request.commodity
            m = mats[commod][-1] 
            mats[commod].pop
            responses.append(trades[ii], m)
            self.resource_indexes.remove(m.obj_id)
        self.push_spent(mats)
        print("end get material trades", self.context.time)
        return 

    def accept_material_trades(self, responses): # phase 5.2
        '''
        Accept bid for fuel_incommods

        The number of assemblies to be loaded is the minimum 
        of the number of responses or the number of 
        assemblies the core is missing (full core minus how many 
        assemblies are present). If the number of assemblies to 
        load is greater than 0, then record this number.

        For each trade in the responses, get the commodity requested 
        in the trade and reset the index. 

        If the core is not full, the put the material in the core. 
        If the core is full, the put the material in the fresh 
        fuel inventory. 

        '''
        print("start accept material trades")
        n_load = min(len(responses), self.n_assem_core - self.core.count)
        if n_load > 0:
            ss = str(n_load) + " assemblies"
            #self.record("LOAD", ss)
        for trade in responses:
            commod = trade.request.commodity
            m = trade.request.target
            self.index_res(m, commod)
            if self.core.count < self.n_assem_core:
                self.core.push(m)
            else:
                self.fresh_fuel.push(m)
        print("core:", self.core.count, "fresh:", self.fresh_fuel.count)
        print("end accept material trades", self.context.time)
        return 

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
        npop = min(self.n_assem_batch, self.core.count)
        if (self.n_assem_spent - self.spent_fuel.count) < npop:
            #self.record("DISCHARGE", "failed")
            return False
        #ss = stringstream 
        ss = str(npop) + " assemblies"
        #self.record("DISCHARGE", ss)
        core_pop = self.core.pop_n(npop)
        for ii in range(len(core_pop)):
            self.spent_fuel.push(core_pop[ii])
        for ii in range(len(self.fuel_outcommods)):
            spent_mats = self.peek_spent()
            mats = spent_mats[self.fuel_outcommods[ii]]
            tot_spent = 0
            tot_spent += mats.quantity
            lib.record_time_series("supply"+self.fuel_outcommods[ii], self, tot_spent)
        return True

    def load(self):
        '''
        Determine number of assemblies to load, either the 
        number of assemblies needed for the core less the number 
        already in the core or the number held by the 
        fresh fuel inventory. If no assemblies are needed, then 
        return. 

        Record the number of assemblies that are to be loaded, then move 
        them from the fresh fuel inventory to the core inventory. 
        '''
        n = min(self.n_assem_core-self.core.count, self.fresh_fuel.count)
        if n == 0:
            return
        ss = str(n) + " assemblies"
        #self.record("LOAD", ss)
        assemblies = self.fresh_fuel.pop_n(n)
        for ii in range(len(assemblies)):
            self.core.push(assemblies[ii])


    def transmute(self, n_assem):
        '''
        Get the material composition of the minimum of the 
        number of assemblies specified or the number of 
        assemblies in the core. 

        If there are more assemblies in the core than what will 
        be removed, then rotate the untransmuted materials to the back 
        of the buffer.

        Record the number of assemblies to be transmuted. Transmute the fuel
        by changing the recipe of the material to that of the 
        fuel_outrecipes

        There seem to be two Transmute functions in the cycamore reactor?
        '''
        #print("core inventory before transmuting:", self.core.count)
        old = self.core.pop_n(min(n_assem, self.core.count))
        print("number of assem to transmute:", len(old))
        for ii in range(len(old)):
            self.core.push(old[ii]) 
        print("core inventory:", self.core.count) 
        #if (self.core.count > len(old)):
        #    self.core.push(self.core.pop_n(self.core.count - len(old)))
        ss = str(len(old)) + " assemblies"
        #self.record("TRANSMUTE", ss)
        print(ss)
        for ii in range(len(old)):
            print("call OpenMC")
        return

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
        events = self.context.new_datum("ReactorEvents") # creates tables with name ReactorEvents
        datum = lib.Datum("Event")
        lib.Datum.add_val(datum, "Event", event)
        events.add_val("Value", val)
        events.record()
        return

        
    def index_res(self, m, incommod):
        '''
        For the name of any item in the fuel in_commods list 
        match the name of the commodity given, then 
        the object Id of the material.

        If the name of the given commodity isn't in the 
        fuel in_commods list, then return an error. 
        '''
        self.resource_indexes = {}
        #self.resource_indexes[m.obj_id] = self.fuel_incommods.index(incommod)
        for ii in range(len(self.fuel_incommods)):
            if self.fuel_incommods[ii] == incommod:
                self.resource_indexes[m.obj_id] = ii 
                return
        raise ValueError (
            "openmcyclus.DepleteReactor:DepleteReactor received "\
                "unsupported incommod material"
            )

    def pop_spent(self):
        '''
        For each assembly in the spent fuel inventory, 
        get the commodity name of it, and push the material 
        back to the spent fuel inventory (??).

        Then reverse the order of the material in the 
        mapped materials to put the oldest assemblies 
        first and make sure they get traded away first. 
        '''
        mats = self.spent_fuel.pop_n(self.spent_fuel.count)
        print("Pop_Spent, mats", mats) 
        mapped = {}
        for commod in self.fuel_outcommods:
            mapped[commod] = []
        for ii in range(len(mats)):
            for commod in self.fuel_outcommods:
                mapped[commod].append(mats[ii])
        
        #for it in mapped:
        #    ts.reverse(it.second.begin(), it.second.end())
        return mapped

    def push_spent(self, leftover):
        '''
        Reverse the order of materials in the leftover list

        '''
        for item in leftover:
            #reverse(item.second.begin, item.second.end)
            self.spent_fuel.push(item)

    def peek_spent(self):
        '''
        
        '''
        mapped = {}
        if self.spent_fuel.count > 0:
            mats = self.spent_fuel.pop_n(self.spent_fuel.count)
            for ii in range(len(mats)):
                self.spent_fuel.push(mats[ii])
                commod = self.fuel_outcommods[ii]
                mapped[commod] = mats[ii] # not sure what push_back does
        return mapped