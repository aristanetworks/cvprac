######
v0.7.0
######

2017-03-30

New Modules
^^^^^^^^^^^


Enhancements
^^^^^^^^^^^^

* Add image upgrade feature to api. (`19 <https://github.com/aristanetworks/cvprac/pull/19>`_) [`mharista <https://github.com/mharista>`_]
    Added functions for applying image bundles to devices and adding or removing image bundles from containers. Also added container and image information gathering functions.
* Add deploy_device functionality (`23 <https://github.com/aristanetworks/cvprac/pull/23>`_) [`mharista <https://github.com/mharista>`_]
    Added function deploy_device and helper functions for automated deploying of a device from the a container (for example the Undefined container), to the proper end container. Applies any necessary configlets and optionally an image in the process. Also added new functionality for getting information related to containers and devices (for example getting a devices parent container, or a list of devices in a container). Made task creation optional for calls that would normally create a task. Default behavior is to create the task, but if the user wants to take multiple actions for execution in one task (as done in deploy_device) the user can tell the function not to create the task (essentially what this does is delay the call to saveTopology while adding multiple tempActions).
* Add ability for user to configure log level. (`26 <https://github.com/aristanetworks/cvprac/pull/26>`_) [`mharista <https://github.com/mharista>`_]
    Logging level can now we set during client initialization or changed at any time using a client setter.

Fixed
^^^^^

* Make REST call to addTempAction before saveTopology. (`17 <https://github.com/aristanetworks/cvprac/issues/17>`_)
    New CVP version requires calls to addTempAction before saveTopology or the save will not do anything. In the CVP UI creating a container is the equivalent of addTempAction and then clicking save at the bottom to confirm the container remains is the equivalent of saveTopology.
