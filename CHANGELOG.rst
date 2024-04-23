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

**Changed:**

* Change OpenMC dependency to v0.14.0, which includes adding 
  parameters for using `DepleteReactor` (#18)

**Removed:**

* Remove `check_existing_recipes` method in `DepleteReactor` (#18)

**Fixed:**


v 0.1.0
=========
Initial release 