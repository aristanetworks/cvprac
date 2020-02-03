######
v1.0.2
######

2020-2-3

New Modules
^^^^^^^^^^^

* Added API modules for cancel and delete change controls. (`21102ac <https://github.com/aristanetworks/cvprac/commit/21102ac35d591059d7c2ac26e620d6423e21f275>`_) [`mharista <https://github.com/mharista>`_]
* Add modules for applying configlets to containers and removing configlets from containers. (`89 <https://github.com/aristanetworks/cvprac/pull/89>`_) [`mharista <https://github.com/mharista>`_]
* Add module and test for API endpoint /provisioning/v2/validateAndCompareConfiglets.do. (`93 <https://github.com/aristanetworks/cvprac/pull/93>`_) [`mharista <https://github.com/mharista>`_]
* Updates for CVP 2019. Add search_configlets method. Update how we set the api version. Use pkg_resoureces.parse_version instead of brute force. (`95 <https://github.com/aristanetworks/cvprac/pull/95>`_) [`grybak-arista <https://github.com/grybak-arista>`_]
* Add method and tests for API endpoint /provisioning/getNetElementInfoById.do. (`d26d69f <https://github.com/aristanetworks/cvprac/commit/d26d69f16f13bbacbd72d2ee3ea4ae32c3fd1a98>`_) [`mharista <https://github.com/mharista>`_]
* Add method and tests for resetting a device back to Undefined container. (`fb9a96b <https://github.com/aristanetworks/cvprac/commit/fb9a96b1fbdf04c381460f8aa68a53b2b2ff8c70>`_) [`mharista <https://github.com/mharista>`_]
* Add method for adding configletbuilder. (`97 <https://github.com/aristanetworks/cvprac/pull/97>`_) [`networkRob <https://github.com/networkRob>`_]

Enhancements
^^^^^^^^^^^^

* Add snapshot template key to task list entries for create change control method. (`80 <https://github.com/aristanetworks/cvprac/pull/80>`_) [`mharista <https://github.com/mharista>`_]
* Update add_devices_to_inventory to support multiple devices in one call. (`84 <https://github.com/aristanetworks/cvprac/pull/84>`_) [`grybak-arista <https://github.com/grybak-arista>`_]
* Add ability to set API request timeout via client connect method. (`92 <https://github.com/aristanetworks/cvprac/pull/92>`_) [`mharista <https://github.com/mharista>`_]
* Add return value for cancel_task method and update necessary tests. (`2356d59 <https://github.com/aristanetworks/cvprac/commit/2356d59e0e0fb9db2de9e8b3f123ad31c97e5cf76>`_) [`mharista <https://github.com/mharista>`_]
* Update existing Change Control APIs and add new ones for 2019.1.0. (`4fddb1e <https://github.com/aristanetworks/cvprac/commit/4fddb1ebb250f4d58dcd59ed952bdd12b3e04e7d>`_) [`mharista <https://github.com/mharista>`_]
* Update change_control_available_tasks to use standard get_tasks_by_status for 2019.1. (`06eb19a4 <https://github.com/aristanetworks/cvprac/commit/06eb19a4d6b3db3c22b92c4dc5452e5241f2e00c>`_) [`mharista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fix issue where requests fail if response has no json payload. (`81 <https://github.com/aristanetworks/cvprac/pull/81>`_) [`mharista <https://github.com/mharista>`_]
* Update error handling of unauthorized user for CVP 2019.x. (`f4bf302 <https://github.com/aristanetworks/cvprac/commit/f4bf30283891d41d5a55abe46c80736c7159aca9>`_) [`mharista <https://github.com/mharista>`_]
