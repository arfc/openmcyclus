import numpy as np
import math
import openmc
import openmc.deplete as od

# create model objects and set cross section libraries
uox_model = openmc.Model()
mox_model = openmc.Model()
openmc.config['cross_sections'] = "/home/abachmann@anl.gov/openmc-xs-data/endfb-viii.0-hdf5/cross_sections.xml"

# Define materials
uo2 = openmc.Material(1, "uo2")
uo2.add_nuclide('U235', 0.03)
uo2.add_nuclide('U238', 0.97)
uo2.add_nuclide('O16', 2.0)
uo2.set_density('g/cm3', 10.0)
uo2.volume = 0.4778 # area of circle for fuel
uo2.depletabe =True

zirconium = openmc.Material(name="zirconium")
zirconium.add_element('Zr', 1.0)
zirconium.set_density('g/cm3', 6.6)

water = openmc.Material(name="h2o")
water.add_nuclide('H1', 2.0)
water.add_nuclide('O16', 1.0)
water.set_density('g/cm3', 1.0)
water.add_s_alpha_beta('c_H_in_H2O')

puo2 = openmc.Material(4)
puo2.add_nuclide('Pu239', 0.94)
puo2.add_nuclide('Pu240', 0.06)
puo2.add_nuclide('O16', 2.0)
puo2.set_density('g/cm3', 11.5)

# Create the mixture
mox = openmc.Material.mix_materials([uo2, puo2], [0.97, 0.03], 'wo')
mox.volume = 0.4778 # area of circle for fuel
mox.depleteable=True

uox_model.Materials = openmc.Materials([uo2, zirconium, water])
mox_model.Materials = openmc.Materials([mox, zirconium, water])

# Geometry
fuel_outer_radius = openmc.ZCylinder(r=0.39)
clad_inner_radius = openmc.ZCylinder(r=0.40)
clad_outer_radius = openmc.ZCylinder(r=0.46)

fuel_region = -fuel_outer_radius
gap_region = +fuel_outer_radius & -clad_inner_radius
clad_region = +clad_inner_radius & -clad_outer_radius

uox_fuel = openmc.Cell(name='fuel')
uox_fuel.fill = uo2
uox_fuel.region = fuel_region

mox_fuel = openmc.Cell(name='fuel')
mox_fuel.fill = mox
mox_fuel.region = fuel_region

gap = openmc.Cell(name='air gap')
gap.region = gap_region

clad = openmc.Cell(name='clad')
clad.fill = zirconium
clad.region = clad_region

pitch = 1.26
box = openmc.model.RectangularPrism(width=pitch, height=pitch,
                               boundary_type='reflective')
water_region = -box & +clad_outer_radius
moderator = openmc.Cell(name='moderator')
moderator.fill = water
moderator.region = water_region

uox_universe = openmc.Universe(cells=(uox_fuel, gap, clad, moderator))
mox_universe = openmc.Universe(cells=(mox_fuel, gap, clad, moderator))

uox_model.geometry = openmc.Geometry(uox_universe)
mox_model.geometry = openmc.Geometry(mox_universe)

# Settings
settings = openmc.Settings()
settings.batches = 100
settings.inactive = 10
settings.particles = 1000
settings.output = {'tallies':True}
uox_model.settings = settings
mox_model.settings = settings

# Generate one-group cross section data and flux for each material
uox_cross_sections = od.get_microxs_and_flux(uox_model, 
                                       domains = [uo2], 
                                       chain_file="chain_endfb71_pwr.xml")
clad_cross_sections = od.get_microxs_and_flux(uox_model, 
                                       domains = [clad], 
                                       chain_file="chain_endfb71_pwr.xml")
water_cross_sections = od.get_microxs_and_flux(uox_model, 
                                       domains = [water], 
                                       chain_file="chain_endfb71_pwr.xml")
mox_cross_sections = od.get_microxs_and_flux(mox_model, 
                                       domains = [mox_fuel], 
                                       chain_file="chain_endfb71_pwr.xml")

# save cross sections from UOX model for use in Deplete Reactor
uox_cross_sections[1][0].to_csv("micro_xs.csv")
mox_cross_sections[1][0].to_csv("mox_xs.csv")

# Set up IndependentOperator for each model
uox_ind_op = od.IndependentOperator(uox_model.Materials, 
                                [uox_cross_sections[0][0], clad_cross_sections[0][0], water_cross_sections[0][0]],
                                [uox_cross_sections[1][0], clad_cross_sections[1][0], water_cross_sections[1][0]],
                                "chain_endfb71_pwr.xml")
mox_ind_op = od.IndependentOperator(openmc.Materials([mox]), 
                                [mox_cross_sections[0][0]],
                                mox_cross_sections[1],
                                "chain_endfb71_pwr.xml")

# Perform Depletion for just UOX model
uox_integrator = od.PredictorIntegrator(uox_ind_op,
                                    np.ones(12*3)*30, # 3 cycles of operation
                                   power_density = 46.3, # linear power density in W/g
                                   timestep_units='d')
uox_integrator.integrate()

# Process results
uox_results = od.Results("depletion_results.h5")
uox_spent = uox_results.export_to_materials(-1)

#printing in format for Cyclus recipe
total = 0
weight_frac = 0
pu_frac = 0
for nuclide in uox_spent[0].nuclides:
    total += nuclide.percent
    #if nuclide.percent <= 1e-10:
    #    continue
    Z, A, m = openmc.data.zam(nuclide.name)
    zaid = Z*1e7+A*1e4+m
    print(f"<nuclide>  <id>{int(zaid)}</id> <comp>{nuclide.percent}</comp>  </nuclide>")
    weight_frac += nuclide.percent*A
    if Z == 94:
        pu_frac += nuclide.percent*A
    total += nuclide.percent