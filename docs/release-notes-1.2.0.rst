######
v1.2.0
######

2022-5-20

New Modules
^^^^^^^^^^^

* Added new method for creating TerminAttr enrollment token. (`9bf409b <https://github.com/aristanetworks/cvprac/commit/9bf409b864774490dabac6fdcef24dc3735ad240>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Added new methods for managing tags and workspaces. (`e0b8185 <https://github.com/aristanetworks/cvprac/commit/e0b818597b78345759be20b3319c3d574e56f732>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Additional methods for managing workspaces. (`71eea87 <https://github.com/aristanetworks/cvprac/commit/71eea87a012950165f7e87b2bb8b83556da5b4bf>`_) [`mharista <https://github.com/mharista>`_]
* Added new methods for change control resource APIs. (`d0b1916 <https://github.com/aristanetworks/cvprac/commit/d0b19164012fc6358fb71bdba21ebd44ec126ca2>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Added new methods for change control scheduling and device decommissioning. (`370d02f <https://github.com/aristanetworks/cvprac/commit/370d02fe8a33436337d0866d54a0201f76a5c44b>`_) [`noredistribution <https://github.com/noredistribution>`_]

Enhancements
^^^^^^^^^^^^

* Added ability to run change control tasks sequentially or in parallel. (`5fd48d5e <https://github.com/aristanetworks/cvprac/commit/5fd48d5e33b6f657650b6bde949e202ba644776c>`_) [`mharista <https://github.com/mharista>`_]
* Improved system test setup and base classes. (`36029b5 <https://github.com/aristanetworks/cvprac/commit/36029b5c0f5d47b6cddeca89b33380afb69f2ec2>`_) [`KonikaChaurasiya-GSLab <https://github.com/KonikaChaurasiya-GSLab>`_]
* Do not run getConfigletByName for every configlet to make get_configlets more efficient. (`3c1a3eb <https://github.com/aristanetworks/cvprac/commit/3c1a3eb2ae9ebe2ae3f07835ac86cdbd33d34baa>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Added system tests for new change control resource APIs and more system test infrastructure enhancements. (`4564ef3 <https://github.com/aristanetworks/cvprac/commit/4564ef327f1b8abd743adb791ed742d586fc5587>`_) [`KonikaChaurasiya-GSLab <https://github.com/KonikaChaurasiya-GSLab>`_]
* Added system test for new decommission device APIs. (`4fd4b7f <https://github.com/aristanetworks/cvprac/commit/4fd4b7f476ca08323fdf4c96df41665e7f78ec96>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Documentation format updates. (`ac4f2ff <https://github.com/aristanetworks/cvprac/commit/ac4f2ff8f45fd68b42a5ce8b68e0a565e9dbe8a8>`_) [`tgodaA <https://github.com/tgodaA>`_]
* Assorted system test format updates for various CVP versions support.
* Added support for CVP versions up to CVP 2022.1.0.

Fixed
^^^^^

* Removed timestamp variable declaration from approve change control function. (`2b1e6ac <https://github.com/aristanetworks/cvprac/commit/2b1e6ac44fbc912ea60841eb10ab2d19b1f59c65>`_) [`mharista <https://github.com/mharista>`_]
* Add wrapper function for validate_config that will return the full response data structure. (`0540c7a <https://github.com/aristanetworks/cvprac/commit/0540c7ac64cba0b6a8ad4de00f828519d1d5f557>`_) [`mharista <https://github.com/mharista>`_]
* Fix request headers for CVaaS. (`f57ea4e <https://github.com/aristanetworks/cvprac/commit/f57ea4e6089130eccbc91f6831fbb3d2054020af>`_) [`mharista <https://github.com/mharista>`_]
