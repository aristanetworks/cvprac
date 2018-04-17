######
v0.9.0
######

2018-04-17

New Modules
^^^^^^^^^^^

* Added Inventory handling methods. (`51 <https://github.com/aristanetworks/cvprac/pull/51>`_) [`cheynearista <https://github.com/cheynearista>`_]
    add_device_to_inventory, retry_add_to_inventory, delete_device, delete_devices, get_non_connected_device_count, save_inventory.
* Add basic logout api function. (`d52f4a0 <https://github.com/aristanetworks/cvprac/commit/d52f4a07c49e358d86ca0701d5885cddfd231f98>`_) [`mharista <https://github.com/mharista>`_]
    Added for future enhanced handling of session logout.

Enhancements
^^^^^^^^^^^^

* Add ability to provide a query parameter to get_inventory. (`423d555 <https://github.com/aristanetworks/cvprac/commit/423d555adfd0a015ee96540fdc1048a0e26c5c84>`_) [`mharista <https://github.com/mharista>`_]
    Query string can be used as a match to filter returned inventory list. For example you can filter on a specific version of EOS.
* Add contact info to docs. (`693d3ba <https://github.com/aristanetworks/cvprac/commit/693d3ba57caa72bb326adbae98b64dba8bc0f104>`_) [`mharista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fix get_device_by_name to return only the device with the given FQDN. (`41 <https://github.com/aristanetworks/cvprac/pull/41>`_)
    This was returning all devices that contained the provided name as a string in their data. Now verify the FQDN matches the name before returning.
* Fix get_devices_in_container to only return devices in the specified container. (`2b26d0c <https://github.com/aristanetworks/cvprac/commit/2b26d0cff773ff687e0d7c0460dd64c9927f2383>`_) [`mharista <https://github.com/mharista>`_]
    This was previously returning all devices from get_inventory that matched a query string anywhere in their data instead of specific to the parent container.
* Remove 'id': 1 from data structs in requests. (`52 <https://github.com/aristanetworks/cvprac/pull/52>`_) [`grybak-arista <https://github.com/grybak-arista>`_]
    This key:value being included int he request data causes an error in 2018 versions of CVP.
* Add fix for special characters in object names in url. (`53 <https://github.com/aristanetworks/cvprac/pull/53>`_) [`mharista <https://github.com/mharista>`_]
    Special characters in request parameters (for example a container name Rack2+_DC11) would cause unexpected results. This are now properly escaped for HTTP.
