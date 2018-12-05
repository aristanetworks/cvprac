######
v1.0.0
######

2018-12-05

New Modules
^^^^^^^^^^^

* Added method for capturing container level snapshot. (`57 <https://github.com/aristanetworks/cvprac/pull/57>`_) [`brokenpackets <https://github.com/brokenpackets>`_]
    capture_container_level_snapshot.
* Added method for getting event by ID. (`58 <https://github.com/aristanetworks/cvprac/pull/58>`_) [`brokenpackets <https://github.com/brokenpackets>`_]
    get_event_by_id.
* Added method for getting device running config. (`3b97ba3 <https://github.com/aristanetworks/cvprac/commit/3b97ba3533ef0783d1a3ef6e5e060949245f4715>`_) [`mharista <https://github.com/mharista>`_]
    get_device_configuration.
* Added methods for change control functionality. (`7e49447 <https://github.com/aristanetworks/cvprac/commit/7e494473cf519a506d0445b4bf8f726fe353b753>`_) [`mharista <https://github.com/mharista>`_]
    get_change_controls, change_control_available_tasks, create_change_control.
* Added method for adding notes to change control. (`e21c0ae <https://github.com/aristanetworks/cvprac/commit/e21c0aeb7d3a6141fc2ab3876906a201ddba3dcd>`_) [`mharista <https://github.com/mharista>`_]
    add_notes_to_change_control.
* Add assorted methods. (`68 <https://github.com/aristanetworks/cvprac/pull/68>`_) [`grybak-arista <https://github.com/grybak-arista>`_]
    get_configlets, get_configlets_by_container_id, get_configlets_by_netelement_id, add_note_to_configlet, get_all_temp_actions,
    get_applied_devices, get_applied_containers, filter_topology, get_default_snapshot_template, capture_container_level_snapshot,
    add_image, save_image_bundle, update_image_bundle, execute_change_control, get_change_control_info.

Enhancements
^^^^^^^^^^^^

* Add flag for create_task to deploy_device. (`59 <https://github.com/aristanetworks/cvprac/pull/59>`_) [`brokenpackets <https://github.com/brokenpackets>`_]
    Flag defaults to True and allows user to decide if they want tasks automatically created when calling deploy_device.
* Allow waiting for task IDs when updating configlets. (`67 <https://github.com/aristanetworks/cvprac/pull/67>`_) [`grybak-arista <https://github.com/grybak-arista>`_]
    Flag for waitForTaskIds parameter added to update_configlet method. Defaults to False.
* Update appropriate APIs and tests to support CVP 2018.2. (`ad7b576 <https://github.com/aristanetworks/cvprac/commit/ad7b576758f6c8aaa839301ca68b4669ac377239>`_) [`mharista <https://github.com/mharista>`_]
    CVP 2018.2 includes large changes to the Restful APIs. Many APIs are deprecated and many APIs return data is slightly different from data returned by 2018.1.
    This update does processing to help mitigate some of these changes by fixing return data of 2018.2 to look more like return data from 2018.1 in cases where
    fields are removed or have their name key changed. Be aware that though this update catches many of these cases it does not catch all.

Fixed
^^^^^

* Fix connection reconnect handling for CVP 2018 support. (`e13dc54 <https://github.com/aristanetworks/cvprac/commit/e13dc546ecccf7fd25fd48458226cbe9c3cf0aa8>`_) [`mharista <https://github.com/mharista>`_]
    Unauthorized handled differently.
