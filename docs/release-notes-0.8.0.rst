######
v0.8.0
######

2017-09-12

New Modules
^^^^^^^^^^^

* Added/updated API function for validating a devices config. (`27 <https://github.com/aristanetworks/cvprac/pull/27>`_) (`updates <https://github.com/aristanetworks/cvprac/commit/c5466163a5d79ffb4cd0ee18d1e47371b7264c35>`_)
    New function in API that will return True if the passed in device is running a valid config. Will return False and log error messages if the device validation check fails.
* Add Jenkins integration and pre-commit hook. (`31 <https://github.com/aristanetworks/cvprac/pull/31>`_) [`jerearista <https://github.com/jerearista>`_]
* Update client protocol default to https with http fallback. (`33 <https://github.com/aristanetworks/cvprac/pull/33>`_) [`mharista <https://github.com/mharista>`_]
    With new versions of CVP only supporting https we have changed the default protocol used to https. The protocol parameter passed to the client is no longer used. The client connect will attempt to use https with a fallback of http if it fails to connect via https. A user can force https with no http fallback by providing a path to a valid certificate to the connect method for new parameter cert. Default https connection with no cert provided will use unverified https requests.

Enhancements
^^^^^^^^^^^^

* Added property to CvpClient that stores last node a request was made to. (`34 <https://github.com/aristanetworks/cvprac/pull/34>`_) [`mharista <https://github.com/mharista>`_]
    New last_used_node function will return the last CVP node a request was sent to.

Fixed
^^^^^

* Fixed functions for removing images from devices and containers. (`33 <https://github.com/aristanetworks/cvprac/pull/33>`_) [`mharista <https://github.com/mharista>`_]
    Bugs in the code for removing images was causing system tests to fail due to the system under tests to get out of compliance.
* Removed non-default python logging module. (`38 <https://github.com/aristanetworks/cvprac/pull/38>`_) [`grybak-arista <https://github.com/grybak-arista>`_]
    Using default logging built into python. The non-default module was causing problems in some cases when installing with pip.
