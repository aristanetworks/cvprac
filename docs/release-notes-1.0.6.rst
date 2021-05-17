######
v1.0.6
######

2021-5-17

New Modules
^^^^^^^^^^^

* Started to add api method update_configlet_builder and add test.. (`a32dd7a <https://github.com/aristanetworks/cvprac/commit/a32dd7ae00f73d887eb7ae06635c0102be80945d>`_) [`dbm79 <https://github.com/dbm79>`_]
* Added function and test for API endpoint updateReconcileConfiglet.do. (`7e90de9 <https://github.com/aristanetworks/cvprac/commit/7e90de90c416c7dce750e1e9ae2928794efc2b1f>`_) [`mharista <https://github.com/mharista>`_]

Enhancements
^^^^^^^^^^^^

* Add client handling for new resource API REST bindings that return multiple objects in response data. (`bea2d28 <https://github.com/aristanetworks/cvprac/commit/bea2d282093ceb10085e158acd76ed20c12ae485>`_) [`mharista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fix client logout function to use cvprac client post function instead of session post function. (`abaf257 <https://github.com/aristanetworks/cvprac/commit/abaf2577afb5b9b5e9d99a6b848ca2e987c22e66>`_) [`mharista <https://github.com/mharista>`_]
* Mask localhost/127.0.0.1 with node ip for cb scripts. (`d45ac6e <https://github.com/aristanetworks/cvprac/commit/d45ac6e06394c05bb4c5584a14f262e3c814eef5>`_) [`Rajat Bajaj <https://github.com>`_]
* Updating info string to tackle backend inconsistent state when moving devices from the Undefined container. (`82ea8b9 <https://github.com/aristanetworks/cvprac/commit/82ea8b922c57bb86719351c55a2f8a671d49e0db>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Remove CVaaS un/pw login. Only API tokens for CVaaS now. (`f9fd6b5 <https://github.com/aristanetworks/cvprac/commit/f9fd6b51698de9afcb6112c0180185a6e76f4e5c>`_) [`mharista <https://github.com/mharista>`_]
* Update redundant functions to self reference. (`0095b00 <https://github.com/aristanetworks/cvprac/commit/0095b0001839723680caea62323cae56a130ad32>`_) [`mharista <https://github.com/mharista>`_]
* Add exception when attempting to delete container with children for CVP versions 2020.1 and beyond. (`35bb566 <https://github.com/aristanetworks/cvprac/commit/35bb56609d6d986b11dff11b4454e2cdc120ccd9>`_) [`mharista <https://github.com/mharista>`_]
