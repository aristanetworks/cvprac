######
v1.0.4
######

2020-8-18

New Modules
^^^^^^^^^^^

* Add function and tests for getConfigletsAndAssociatedMappers.do API. (`d8e9316 <https://github.com/aristanetworks/cvprac/commit/d8e93168a3691f466f10e49a98c32b87ceb2aaa1>`_) [`mharista <https://github.com/mharista>`_]
* Add function and tests for getImageBundleByContainerId.do API. (`131783c <https://github.com/aristanetworks/cvprac/commit/131783ce4efa2afb4ec00c0cb9e6922c38eb4258>`_) [`mharista <https://github.com/mharista>`_]
* Add functions for user management APIs. (`113 <https://github.com/aristanetworks/cvprac/pull/113>`_) [`noredistribution <https://github.com/noredistribution>`_]
* Add function for delete user API and update user handling tests. (`681dc06 <https://github.com/aristanetworks/cvprac/commit/681dc0601cee2c10d1948284e68ba67baed7049e>`_) [`mharista <https://github.com/mharista>`_]

Enhancements
^^^^^^^^^^^^

* Add delete() function to client for DELETE REST API requests. (`a8cdc82 <https://github.com/aristanetworks/cvprac/commit/a8cdc8274f7764021254bb1ffa87d26d368a8393>`_) [`mharista <https://github.com/mharista>`_]
* Add new API version (v4) for new CVP version 2020.2. (`546a119 <https://github.com/aristanetworks/cvprac/commit/546a1192e70ed9b77615a41837fecbeb729ca371>`_) [`mharista <https://github.com/mharista>`_]
* Update delete_devices() function for new CVP version. (`819c073 <https://github.com/aristanetworks/cvprac/commit/819c073bb60696ced61cf128348e59919dd0b3fa>`_) [`mharista <https://github.com/mharista>`_]
* Update get_device_configuration() function for new CVP version. (`9ef992a <https://github.com/aristanetworks/cvprac/commit/9ef992a4f08f67d79d0899d3627a240ca1f90621>`_) [`mharista <https://github.com/mharista>`_]
* Update apiversion variable to be float instead of string for better conditional handling. (`425f395 <https://github.com/aristanetworks/cvprac/commit/425f3959944c685e6698220e9f213631ca61679c>`_) [`mharista <https://github.com/mharista>`_]
* Add initial CVaaS support for CVP local users. (`3c28251 <https://github.com/aristanetworks/cvprac/commit/3c28251f3bb16fc26901318ecbf554ce324082d9>`_) [`mharista <https://github.com/mharista>`_]
* Improve efficiency of get_inventory() by removing extra API calls. (`b9c0e69 <https://github.com/aristanetworks/cvprac/commit/b9c0e6909296e851468ba55c45938575cda3e6d6>`_) [`mharista <https://github.com/mharista>`_]
* Improve efficiency of get_containers() function and add support for using CVaaS API token. (`82effac <https://github.com/aristanetworks/cvprac/commit/82effac800ea4cc855f5309c0b4baa490df77b88>`_) [`mharista <https://github.com/mharista>`_]
* Update documentation with API version handling info and different connection type examples. (`c714262 <https://github.com/aristanetworks/cvprac/commit/c714262290bab2752a64046f1d0955439b7ba94c>`_) [`mharista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fix issue with different field parameters in image object vs image bundle object. (`7d1b845 <https://github.com/aristanetworks/cvprac/commit/7d1b84522413b21180033cfda945ad25d62a3f30>`_) [`mharista <https://github.com/mharista>`_]
* Fix issue with 'errorCode' string being in request response text. (`7ea6570 <https://github.com/aristanetworks/cvprac/commit/7ea657013ea3f8bb9007d1e926458209254b4cc9>`_) [`mharista <https://github.com/mharista>`_]
