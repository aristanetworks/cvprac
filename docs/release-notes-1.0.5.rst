######
v1.0.5
######

2021-2-11

Enhancements
^^^^^^^^^^^^

* Never fallback to HTTP in case of connection failure. (`c2e6d97 <https://github.com/aristanetworks/cvprac/commit/c2e6d9770efb5eb56e3c4519db22281f6845b6c1>`_) [`freedge <https://github.com/freedge>`_]
* Add client handling for CVP 2020.3. Update get_logs_by_id for CVP 2020.3. (`ac23188 <https://github.com/aristanetworks/cvprac/commit/ac2318890dfd3af437411363d3b782a9d28dfac7>`_) [`mharista <https://github.com/mharista>`_]
* Add more detailed docstring to check_compliance function. (`e1ad7e8 <https://github.com/aristanetworks/cvprac/commit/e1ad7e813a6c7e557c27e068591ae7a9e527927f>`_) [`mharista <https://github.com/mharista>`_]
* Update get_device_by_name and get_device_by_mac to use search_topology instead of get_inventory. (`a2b35cb <https://github.com/aristanetworks/cvprac/commit/a2b35cb0609957b6178c549fb6a33e6eb59eeb5e>`_) [`mharista <https://github.com/mharista>`_]
* Add general support for using api tokens for access to REST API. (`409b68d <https://github.com/aristanetworks/cvprac/commit/409b68d905850bd471b0355b2574cf4497579ada>`_) [`mharista <https://github.com/mharista>`_]
* Updated/Enhanced user APIs. (`0c652ea <https://github.com/aristanetworks/cvprac/commit/0c652ea850c9bd4565c5e0f10f1161ae9984cc3f>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Update approve_change_control to provide current time timestamp as default. (`fb13861 <https://github.com/aristanetworks/cvprac/commit/fb1386121b0114bfa06134f7dff4a4efa77a93b6>`_) [`colinmacgiolla <https://github.com/colinmacgiolla>`_]
