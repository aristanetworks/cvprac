# cvprac labs

The following lab examples will walk through the most commonly used REST API calls using cvprac
to help users interact with Arista CloudVision easily and automate the provisioning of network devices.

## Authentication

There are two ways to authenticate using the REST APIs:
- user/password (on-prem only)
- service account token (available on CVP 2020.3.0+ and CVaaS)

### User/password authentication

```python
from cvprac.cvp_client import CvpClient
clnt = CvpClient()
clnt.connect(['10.83.13.33'],'cvpadmin', 'arastra')
```

### Service account token authentication

To access the CloudVision as-a-Service and send API requests, “Service Account Token” is needed.
After obtaining the service account token, it can be used for authentication when sending API requests.

Service accounts can be created from the Settings page where a service token can be generated as seen below:

![serviceaccount1](./static/serviceaccount1.png)
![serviceaccount2](./static/serviceaccount2.png)
![serviceaccount3](./static/serviceaccount3.png)

The token should be copied and saved to a file that can later be referred to.

```python
from cvprac.cvp_client import CvpClient
clnt = CvpClient()
with open("token.tok") as f:
    token = f.read().strip('\n')
clnt.connect(nodes=['www.arista.io'], username='', password='', is_cvaas=True, api_token=token)
```

>NOTE In case of CVaaS the `is_cvaas` parameters has to be set to `True`

Service accounts are supported on CVP on-prem starting from `2020.3.0`. More details in the [TOI](https://eos.arista.com/toi/cvp-2020-3-0/service-accounts/) and the [CV config guide](https://www.arista.com/en/cg-cv/cv-service-accounts).

```python
from cvprac.cvp_client import CvpClient

with open("token.tok") as f:
    token = f.read().strip('\n')

clnt = CvpClient()
clnt.connect(nodes=['10.83.13.33'], username='',password='',api_token=token)
```