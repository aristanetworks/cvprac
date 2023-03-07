######
v1.3.0
######

2023-2-28

New Modules
^^^^^^^^^^^

* Added functions for role APIs. (`238 <https://github.com/aristanetworks/cvprac/pull/238>`_) [`vmmor <https://github.com/vmmor>`_]
* Added support for proxies. (`243 <https://github.com/aristanetworks/cvprac/pull/243>`_) [`mharista <https://github.com/mharista>`_]

Enhancements
^^^^^^^^^^^^

* Add timeouts as configurable parameters for system tests. (`228 <https://github.com/aristanetworks/cvprac/pull/228>`_) [`mharista <https://github.com/mharista>`_]
* Update delete_change_control() to call new Resource API endpoint for supported versions of CVP. (`230 <https://github.com/aristanetworks/cvprac/pull/230>`_) [`mharista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fixed format to allow usage of latest requests package. (`227 <https://github.com/aristanetworks/cvprac/pull/227>`_) [`mharista <https://github.com/mharista>`_]
* Fixed Service Account functions to use State endpoints instead of Config endpoints. (`235 <https://github.com/aristanetworks/cvprac/pull/235>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Handle case for get_parent_container_for_device() returning None within reset_device(). (`240 <https://github.com/aristanetworks/cvprac/pull/240>`_) [`Shivani-chourasiya <https://github.com/Shivani-chourasiya>`_]

Documentation
^^^^^^^^^^^^^

* Add end to end provisioning example for ATD. (`229 <https://github.com/aristanetworks/cvprac/pull/229>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Add example to list applied devices and containers for specified configlet. (`241 <https://github.com/aristanetworks/cvprac/pull/241>`_) [`noredistribution <https://github.com/noredistribution>`_]
