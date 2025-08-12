======================
OpenMCyclus Change Log
======================

Since last release:
===================

**Added:**

* Added `CHANGELOG.rst`, `.gitignore`, `CONTRIBUTING.rst`, 
  and unit tests for `openmcyclus.Depletion` class. Also
  added files for better reproduction of comparison benchmar  (#18)
* Add input parameters to `DepleteReactor` for the thermal 
  power (instead of just using `power_cap`) and flux 
  (required input for running OpenMC with new version) (#18)
* Add CI test to check if CHANGELOG has been updated (#21)
* Added snapshot_inv() and init_inv() to DepleteReactor.py (#23)

**Changed:**

* Change OpenMC dependency to v0.14.0, which includes adding 
  parameters for using `DepleteReactor` (#18)
* Simplify CI build environment, using conda builds instead of 
  building from source (#21)
* Depletion time steps are based on `dt` parameter of Cyclus 
  input (which is in seconds) instead of assuming 30 day time steps (#22)


**Removed:**

* Remove `check_existing_recipes` method in `DepleteReactor` (#18)
* Remove various files in repo that are no longer used for building 
  CI environment (#21)

**Fixed:**

* Fixed the sudden loss of core count in the Tick step when the <explicit_inventroy> flag is on.

v 0.1.0
=========
Initial release 
