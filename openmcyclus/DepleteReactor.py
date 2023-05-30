from cyclus.agents import Facility
from cyclus import lib
import cyclus.typesystem as ts
import math


class DepleteReactor(Facility):
    '''
    Archetype class to model a reactor facility that is
    coupled to the stand alone depletion solver in OpenMC.
    With the exception of the depletion solver, this
    archetype has the same functionality as the
    cycamore:Reactor archetype.
    '''

    fuel_incommods = ts.VectorString(
        doc="Fresh fuel commodity",
        tooltip="Name of commodity requested",
        uilabel="Input Commodity",
    )

    fuel_inrecipes = ts.VectorString(
        doc="Fresh fuel recipe",
        tooltip="Fresh fuel recipe",
        uilabel="Input commodity recipe"
    )

    fuel_prefs = ts.VectorDouble(
        doc="Fuel incommod preference",
        tooltip="Fuel incommod preference",
        uilabel="Fuel incommod preference",
        default=[]
    )

    fuel_outcommods = ts.VectorString(
        doc="Spent fuel commodity",
        tooltip="Name of commodity to bid away",
        uilabel="Output Commodity",
        uitype="outcommodity",
    )

    fuel_outrecipes = ts.VectorString(
        doc="Spent fuel recipe",
        tooltip="Spent fuel recipe",
        uilabel="Output commodity recipe"
    )

    assem_size = ts.Double(
        doc="Mass (kg) of a single fuel assembly",
        tooltip="Mass (kg) of a single fuel assembly",
        uilabel="Assembly Size",
        units="kg",
        default=0
    )

    cycle_time = ts.Double(
        doc="Amount of time between requests for new fuel",
        tooltip="Amount of time between requests for new fuel",
        uilabel="Cycle Time",
        units="months",
        default=0
    )

    refuel_time = ts.Int(
        doc="Time steps for refueling",
        tooltip="Time steps for refueling",
        uilabel="refueltime",
        default=0
    )

    n_assem_core = ts.Int(
        doc="Number of assemblies in a core",
        tooltip="Number of assemblies in a core",
        uilabel="n_assem_core",
        default=0
    )

    n_assem_batch = ts.Int(
        doc="Number of assemblies per batch",
        tooltip="Number of assemblies per batch",
        uilabel="n_assem_batch",
        default=0
    )

    n_assem_fresh = ts.Int(
        doc="Number of fresh fuel assemblies to keep on hand "
        "if possible",
        default=0,
        range=[0, 3],
        uilabel="Minimum fresh fuel inventory",
        units="assemblies"
    )

    n_assem_spent = ts.Int(
        doc="Number of spent fuel assemblies that can be stored "
        "on-site before reactor operation stalls",
        default=10000000,
        uilabel="Maximum spent fuel inventory",
        units="assemblies"
    )

    power_cap = ts.Double(
        doc="Maximum amount of power (MWe) produced",
        tooltip="Maximum amount of power (MWe) produced",
        uilabel="power_cap",
        units="MW",
        default=0
    )

    decom_transmute_all = ts.String(
        doc="If true, the archetype transmutes all assemblies "
        "upon decommisioning. If false, the archetype only "
        "transmutes half.",
        default=0
    )

    fresh_fuel = ts.ResBufMaterialInv()
    core = ts.ResBufMaterialInv()
    spent_fuel = ts.ResBufMaterialInv()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fresh_fuel_entry_times = []
        self.core_entry_times = []
        self.fresh_fuel.capacity = self.assem_size * self.n_assem_fresh
        self.core.capacity = self.assem_size * self.n_assem_core
        self.spent_fuel.capacity = self.assem_size * self.n_assem_spent
        self.cycle_step = 0
        self.power_name = "power"
        self.discharged = False
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
        print("time:", self.context.time, "tick")
        if self.retired():
            print("time:", self.context.time, "retired")
        #    self.record("RETIRED", "")
            if self.context.time == self.exit_time + 1:
                if self.decom_transmute_all == 1:
                    self.transmute(math.ceil(self.n_assem_core))
                else:
                    self.transmute(math.ceil(self.n_assem_core / 2))

            while self.core.count > 0:
                if self.discharge() == False:
                    break
            print("time:", self.context.time, "end discharge loop")
            while (
                    self.fresh_fuel.count > 0) and (
                    self.spent_fuel.space >= self.assem_size):
                self.spent_fuel.push(self.fresh_fuel.pop())

            print(
                "time:",
                self.context.time,
                "decommission?",
                self.check_decommission_condition())
            if self.check_decommission_condition():
                self.decommission()

        print("time:", self.context.time, "end retired loop")
        if self.cycle_step == self.cycle_time:
            print(
                "time:",
                self.context.time,
                "transmute",
                math.ceil(
                    self.n_assem_batch))
            self.transmute(math.ceil(self.n_assem_batch))

        if (self.cycle_step >= self.cycle_time) and (self.discharged == False):
            self.discharged = self.discharge()

        if self.cycle_step >= self.cycle_time:
            print("time:", self.context.time, "load")
            print("time:", self.context.time, self.core.count)
            print("time:", self.context.time, self.fresh_fuel.count)
            self.load()

        # lib.Logger('5', str("DepleteReactor" + str(self.power_cap) + "is ticking"))
        print("time:", self.context.time, "end tick")
        return

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
        print("time:", self.context.time, "tock")
        if self.retired():
            return

        if (
            self.cycle_step >= self.cycle_time +
            self.refuel_time) and (
            self.core.count == self.n_assem_core) and (
                self.discharged):
            self.discharged = False
            self.cycle_step = 0

        if (self.cycle_step == 0) and (self.core.count == self.n_assem_core):
            # self.record("CYCLE_START", "")
            print("Cycle start")

        if (self.cycle_step >= 0) and (self.cycle_step < self.cycle_time) and (
                self.core.count == self.n_assem_core):
            lib.record_time_series(lib.POWER, self, self.power_cap)
            lib.record_time_series("supplyPOWER", self, int(self.power_cap))
            print("time:", self.context.time, "record 100 power")
        else:
            lib.record_time_series(lib.POWER, self, 0)
            lib.record_time_series("supplyPOWER", self, int(0))
            print("time:", self.context.time, "record 0 power")

        if (self.cycle_step > 0) or (self.core.count == self.n_assem_core):
            self.cycle_step += 1
            print(
                "time:",
                self.context.time,
                "end tock, cycle step:",
                self.cycle_step)
        return

    def enter_notify(self):
        '''
        Calls the enter_notify method of the parent class. 
        Also defines a list for the input commodity preferences if 
        not are provided by the user. 
        '''
        super().enter_notify()
        if len(self.fuel_prefs) == 0:
            self.fuel_prefs = [1] * len(self.fuel_incommods)

    def check_decommission_condition(self):
        '''
        If the core and the spent fuel are empty, then the core can be
        decommissioned.

        Returns:
        --------
        Bool: True if conditions are met, otherwise False
        '''
        print("time:", self.context.time, "core count:", self.core.count)
        if (self.core.count == 0) and (self.spent_fuel.count == 0):
            return True
        else:
            return False

    def get_material_requests(self):  # phase 1
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

        Create a request portfolio for each assembly needed to be ordered.
        Create an untracked material for each possible in commodity that
        can be used to meet the demand of each assembly. Set up a mutual request
        (logic OR) for each material that can meet a single assembly demand.
        Apply the mass constraint of an assembly size for each assembly to
        order.

        Returns:
        --------
        ports: list of dictionaries
            Format: [{"commodities":
                      [{commod_name(str):Material object, 
                        "preference":int/float}, ...],
                      "constraints:int/float}, ...]
            Defines the request portfolio for the facility.
        '''
        ports = []
        n_assem_order = self.n_assem_core - self.core.count + \
            self.n_assem_fresh - self.fresh_fuel.count
        print(
            "time:",
            self.context.time,
            "request",
            n_assem_order,
            "assemblies")
        if self.exit_time != -1:
            time_left = self.exit_time - self.context.time + 1
            time_left_cycle = self.cycle_time + self.refuel_time - self.cycle_step
            n_cycles_left = (time_left - time_left_cycle) / \
                (self.cycle_time + self.refuel_time)
            n_cycles_left = math.ceil(n_cycles_left)
            n_need = max(
                0,
                n_cycles_left *
                self.n_assem_batch -
                self.n_assem_fresh +
                self.n_assem_core -
                self.core.count)
            n_assem_order = min(n_assem_order, n_need)

        if n_assem_order == 0 or self.retired():
            return ports

        for ii in range(n_assem_order):
            port = []
            for jj in range(0, len(self.fuel_incommods)):
                commod = self.fuel_incommods[jj]
                pref = self.fuel_prefs[jj]
                recipe = self.context.get_recipe(self.fuel_inrecipes[jj])
                material = ts.Material.create_untracked(
                    self.assem_size, recipe)
                port.append({commod: material, "preference": pref})
                lib.record_time_series(
                    "demand" + commod, self, self.assem_size)
            ports.append({"commodities": port, "constraints": self.assem_size})
        print("time:", self.context.time, "finish get_material_requests")
        print("request portfolio:", ports, len(ports))
        return ports

    def get_material_bids(self, requests):  # phase 2
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

        Parameters:
        -----------
        requests: dict
            dictionary of requests, given by Cyclus, not to be defined by the user.

        Returns:
        --------
        port: dict
            dictionary of materials held by facility that meets a request 
            from another facility
        '''
        print("time:", self.context.time, "start get material_bids")
        got_mats = False
        bids = []
        port = []
        for commod_index, commod in enumerate(self.fuel_outcommods):
            reqs = requests[commod]
            print("time:", self.context.time, "reqs:", reqs)
            if len(reqs) == 0:
                continue
            elif (got_mats == False):
                all_mats = self.peek_spent()
            if len(all_mats) == 0:
                tot_qty = 0
                continue
            if commod in all_mats:
                mats = [all_mats[commod]]

            else:
                mats = []
            print(
                "time:",
                self.context.time,
                "mats to trade matching request commod:",
                mats)
            if len(mats) == 0:
                continue

            recipe_comp = self.context.get_recipe(
                self.fuel_outrecipes[commod_index])

            for req in reqs:
                tot_bid = 0
                for jj in range(len(mats)):
                    tot_bid += mats[jj].quantity
                    qty = min(req.target.quantity, self.assem_size)
                    mat = ts.Material.create_untracked(qty, recipe_comp)
                    for kk in range(self.spent_fuel.count):
                        bids.append({'request': req, 'offer': mat})
                    if tot_bid >= req.target.quantity:
                        break
            tot_qty = 0
            for mat in mats:
                tot_qty += mat.quantity
        if len(bids) == 0:
            return

        port = {'bids': bids}
        print("time:", self.context.time, "portfolio:", port)
        print("time:", self.context.time, "respond", len(bids), "assemblies")
        return port

    def get_material_trades(self, trades):  # phase 5.1
        '''
        Trade away material in the spent_fuel material buffer.

        Pull out the material from spent fuel inventory
        For each trade, get the commodity name, get the
        composition of the trade.

        Then trade the materials from the spent fuel inventory.

        Parameters:
        -----------
        trades: tuple
            tuple of material objects requested matched to the 
            material responses

        Returns:
        --------
        responses: dict
            dictionary of {Material object:Material object}. The 
            key is the Material request being matched. The value is the 
            Material in the spent fuel inventory
        '''
        responses = {}
        mats = self.pop_spent()
        print(
            "time:",
            self.context.time,
            "trade away",
            len(trades),
            "assemblies")
        print(trades)
        for ii in range(len(trades)):
            print("time:", self.context.time, "number of trades:", len(trades))
            print(trades[ii])
            commodity = trades[ii].request.commodity
            mat = mats[commodity].pop(-1)
            responses[trades[ii]] = mat
            self.resource_indexes.pop(mat.obj_id)
        self.push_spent(mats)
        print(responses)

        return responses

    def accept_material_trades(self, responses):  # phase 5.2
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

        Parameters:
        -----------
        responses: dict
            dictionary of {Material object:Material object}. The 
            key is the Material request being matched. The value is the 
            Material in the spent fuel inventory

        
        '''
        print("time:", self.context.time, "responses:", responses)
        # min(len(responses), self.n_assem_core - self.core.count)
        n_load = len(responses)
        print("time:", self.context.time, "accept", n_load, "assemblies")
        if n_load > 0:
            ss = str(n_load) + " assemblies"
            # self.record("LOAD", ss)
        for trade in responses:
            print(trade.request.commodity, trade.request.preference, trade.amt)
            commodity = trade.request.commodity
            material = trade.request.target
            self.index_res(material, commodity)
            if self.core.count < self.n_assem_core:
                self.core.push(material)
            else:
                self.fresh_fuel.push(material)

        print("core:", self.core.count, "fresh:", self.fresh_fuel.count)
        return

    def retired(self):
        '''
        Determine if the prototype is retired

        Return:
        -------
        Bool: true if the conditions are met, False if they aren't met
        '''
        if (self.exit_time != -1) and (self.context.time > self.exit_time):
            return 1
        else:
            return 0

    def discharge(self):
        '''
        Determine the number of assemblies to discharge. If the space for 
        spent fuel assemblies is less than the number that need 
        to be discharged, then don't discharge and return false

        Record the number of assemblies discharged. 

        Remove the correct number of assemblies from the core.
        Get the name of each spent fuel assembly. Then get the 
        mass of each spent fuel commodity discharged. Return true if the 
        fuel has been discharged. 

        Returns:
        --------
        Bool: True if fuel is discharged, false if fuel is not discharged.
        '''
        npop = min(self.n_assem_batch, self.core.count)
        if (self.n_assem_spent - self.spent_fuel.count) < npop:
            # self.record("DISCHARGE", "failed")
            return False

        ss = str(npop) + " assemblies"
        # self.record("DISCHARGE", ss)
        print("time:", self.context.time, "discharge", ss)
        print(self.spent_fuel.count, self.core.count)
        self.spent_fuel.push_many(self.core.pop_n(npop))
        print(self.spent_fuel.count, self.core.count)
        print(self.spent_fuel.peek().comp())
        
        for ii in range(len(self.fuel_outcommods)):
            spent_mats = self.peek_spent()
            tot_spent = 0
            if self.fuel_outcommods[ii] in spent_mats:
                mats = spent_mats[self.fuel_outcommods[ii]]
                tot_spent += mats.quantity
                lib.record_time_series(
                    "supply" + self.fuel_outcommods[ii], self, tot_spent)

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
        n = min((self.n_assem_core - self.core.count), self.fresh_fuel.count)
        print("time:", self.context.time, "load", n, "assemblies")
        if n == 0:
            return
        ss = str(n) + " assemblies"
        #self.record("LOAD", ss)
        self.core.push_many(self.fresh_fuel.pop_n(n))
        return 

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

        Parameters:
        -----------
        n_assem: int
            Number of assemblies to be transmuted
        '''
        old = self.core.pop_n(min(n_assem, self.core.count))
        self.core.push_many(old)
        if self.core.count > len(old):
            self.core.push_many(self.core.pop_n(self.core.count - len(old)))

        ss = str(len(old)) + " assemblies"
        # self.record("TRANSMUTE", ss)
        print("time:", self.context.time, "transmute", ss)
        for ii in range(len(old)):
            print("call OpenMC")
            old[ii].transmute(self.context.get_recipe(self.get_recipe(old[ii],'out')))
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
            value of event to be recorded
        '''
        events = self.context.new_datum(
            "ReactorEvents")  # creates tables with name ReactorEvents
        datum = lib.Datum("Event")
        lib.Datum.add_val(datum, "Event", event)
        events.add_val("Value", val)
        events.record()
        return

    def index_res(self, material, incommod):
        '''
        For the name of any item in the fuel in_commods list
        match the name of the commodity given, then
        the object Id of the material.

        If the name of the given commodity isn't in the
        fuel in_commods list, then return an error.

        Parameters:
        -----------
        material: Material
            Cyclus Material object to be checked 
        incommod: str
            commodity name to compare against
        '''
        try:
            for ii in range(len(self.fuel_incommods)):
                if self.fuel_incommods[ii] == incommod:
                    self.resource_indexes[material.obj_id] = ii
                    return
        except BaseException:
            raise ValueError(
                "openmcyclus.DepleteReactor:DepleteReactor received "
                "unsupported incommod material"
            )

    def pop_spent(self):
        '''
        For each assembly in the spent fuel inventory,
        get the commodity name of it, and push the material
        back to the spent fuel inventory.

        Then reverse the order of the material in the
        mapped materials to put the oldest assemblies
        first and make sure they get traded away first.

        Returns:
        --------
        mapped: dict
            Keys are the commodity names (str) and the values are 
            lists of Material objects from the spent fuel inventory
        '''
        mats = self.spent_fuel.pop_n(self.spent_fuel.count)
        mapped = {}
        for commod in self.fuel_outcommods:
            mapped[commod] = []
        for ii in range(len(mats)):
            commod = self.get_commod(mats[ii], 'out')
            mapped[commod].append(mats[ii])
        print("time:", self.context.time, "pop_spent mapped:", mapped)
        return mapped

    def push_spent(self, leftover):
        '''
        Reverse the order of materials in the leftover list

        Parameters:
        -----------
        leftover: dict
            Keys are the commodity names (str). Values are a list of 
            Material objects. 
        '''
        for commod in leftover:
            leftover[commod].reverse
            for material in leftover[commod]:
                self.spent_fuel.push(material)
        return

    def peek_spent(self):
        '''
        Creates a dictionary of the materials in the spent 
        fuel inventory based on their commodity name. 

        Returns:
        --------
        mapped: dict
            Keys are the commodity names of the spent fuel. 
            Values are the Materials with the given commodity names. 

        '''
        print("peek_spent")
        mapped = {}
        #for commod in self.fuel_outcommods:
        #    mapped[commod] = []
        if self.spent_fuel.count > 0:
            mats = self.spent_fuel.pop_n(self.spent_fuel.count)
            self.spent_fuel.push_many(mats)
            for ii in range(len(mats)):
                commod = self.get_commod(mats[ii], 'out')
                print("get_commod", commod, mats[ii])
                mapped[commod].append(mats[ii])
        print(mapped)
        return mapped

    def get_commod(self, material, flow):
        '''
        Get the index in fuel_incommods or fuel_outcommods
        corresponding to the object id of a material

        Parameters:
        -----------
        material: Material obj
            Material object to be queried 
        flow: str
            input or output commodity. "in" if input, "out"
            if output commodity. 

        Return:
        -------
        string 
            name of commodity for the queried material
        '''
        ii = self.resource_indexes[material.obj_id]
        if flow == 'in':
            return self.fuel_incommods[ii]
        elif flow == 'out':
            return self.fuel_outcommods[ii]

    def get_recipe(self, material, flow):
        '''
        Get the index in fuel_inrecipes or fuel_outrecipes
        corresponding to the object id of a material

        Parameters:
        -----------
        material: Material obj
            Material object to be queried 
        flow: str
            input or output recipe. "in" if input, "out"
            if output recipt. 

        Return:
        -------
        string 
            name of recipe for the queried material
        '''
        ii = self.resource_indexes[material.obj_id]
        if flow == 'in':
            return self.fuel_inrecipes[ii]
        elif flow == 'out':
            return self.fuel_outrecipes[ii]

    def get_pref(self, material):
        '''
        Get the index in fuel_prefs
        corresponding to the object id of a material

        Parameters:
        -----------
        material: Material obj
            Material object to be queried. 

        Return:
        -------
        string 
            preference for the queried material
        '''
        ii = self.resource_indexes[material.obj_id]
        return self.fuel_prefs[ii]
