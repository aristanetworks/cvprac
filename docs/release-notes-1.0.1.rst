######
v1.0.1
######

2019-1-16

New Modules
^^^^^^^^^^^

* Add cancel_image API method for removing an added image before it is saved. (`76 <https://github.com/aristanetworks/cvprac/pull/76>`_) [`mharista <https://github.com/mharista>`_]
    Used in system tests for add_image to reset the CVP node under test to its original state.
* Add delete_image_bundle API method for removing an image bundle. (`76 <https://github.com/aristanetworks/cvprac/pull/76>`_) [`mharista <https://github.com/mharista>`_]
    Used in system tests for add_update_delete_image_bundle to reset the CVP node under test to its original state.

Enhancements
^^^^^^^^^^^^

* Updated all necessary modules and tests to support Python 3. (`76 <https://github.com/aristanetworks/cvprac/pull/76>`_) [`mharista <https://github.com/mharista>`_]
* Updated add_image method to use cvp_client object. (`76 <https://github.com/aristanetworks/cvprac/pull/76>`_) [`mharista <https://github.com/mharista>`_]
* Updated system tests to put CVP node under test back into its original state. (`76 <https://github.com/aristanetworks/cvprac/pull/76>`_) [`mharista <https://github.com/mharista>`_]

Fixed
^^^^^

* Fixed usages of urllib quote_plus method to support Python 3. (`815ec47 <https://github.com/aristanetworks/cvprac/commit/815ec478409473a2259669594a6710895e908726>`_) [`mharista <https://github.com/mharista>`_]
    Python 2 vs Python 3 require importing the method from different modules.
* Fixed formatting issues with client _make_request that were causing systests ran with Python 3 to fail. (`76 <https://github.com/aristanetworks/cvprac/pull/76>`_) [`mharista <https://github.com/mharista>`_]
    When running systests with Python 3 the old _make_request was running UnboundLocalError.
