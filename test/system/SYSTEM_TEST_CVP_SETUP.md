# CVP System Test Setup

Prepare a dedicated CloudVision/CVP instance before running `test/system`.
The tests create, edit, execute, cancel, and delete CVP objects, so do not run
them against a shared or production CVP.

## CVP Requirements

- Create a CVP user with `network-admin` permissions.
- Create the same username and password on the test switch. Task execution
  tests fail with `Unauthorized User` if the switch credentials do not match
  the CVP login. **_Note: on Arista Cloud Test, these two steps are already done during lab deployment._**
- Add at least one test device to CVP inventory.
- Move the test device into the `Tenant` container, not `Undefined`.
- Apply at least one normal configlet directly to the test device. Use a
  configlet assigned only to that device when possible, because tests edit
  configlet contents to create tasks.
- Make sure there is no existing `RECONCILE_<device-name>` configlet for the
  test device.
- Make sure the test device has an `Ethernet1` interface. Tag resource tests
  assign and remove tags on `Ethernet1`.
- If you want image tests to exercise apply/remove image bundle paths, create
  at least one image bundle. Otherwise those paths are skipped.

## Fixture

Update `test/fixtures/cvp_nodes.yaml` before running system tests.
- Change the username and password to the user with `network-admin` permissions that
was created during CVP configuration.
- Change `device` to the device hostname that was added to the **Tenant** Container.

```yaml
- node: cvp-hostname-or-ip
  username: CvpRacTest
  password: AristaInnovates
  device: test-device-hostname
  # api_token: optional-valid-token
  # api_token_expired: optional-expired-token
  # is_cvaas: false
  # connect_timeout: 10
  # request_timeout: 30
```

Multiple entries may be listed, but most system tests use the first entry.
Token tests are skipped unless `api_token` or `api_token_expired` is provided.

## Run

Run the full suite of tests.

```bash
make tests
```
