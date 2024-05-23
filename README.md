# 3scale-api-python-crd

3scale client uses CRs for object definition. CRs are processed by 3scale Operator.

[Capabilities documentation](https://github.com/3scale/3scale-operator/blob/master/doc/operator-application-capabilities.md)

## Installing

Install and update using pip:

```bash
pip install 3scale-api-crd
```

Or as a dependency using the pipenv

```bash
pipenv install 3scale-api-crd
```

## Usage

Client supports basic CRUD operations and it generates CRs in Openshift namespace defined by `oc` session.

Basic usage of the client:

```bash
oc login
oc project example
```

```python
import threescale_api_crd

client = threescale_api_crd.ThreeScaleClientCRD(url="myaccount.3scale.net", token="secret_token", ssl_verify=True, ocp_provider_ref="secret_with_credentials")
```
Using of objects are described in [3scale API client README](https://github.com/3scale-qe/3scale-api-python/blob/master/README.md#usage).


## Run the Smoke Tests

To run the tests you need to have installed development dependencies:
```bash
pipenv install --dev
```

and then run the `pytest`:

```bash
pipenv run pytest -m smoke
```

### Integration tests configuration

To run the integration tests you need to set these extra env variables:
```
THREESCALE_PROVIDER_URL='https://example-admin.3scale.net'
THREESCALE_PROVIDER_TOKEN='<test-token>'

THREESCALE_MASTER_URL='https://master.3scale.net'
THREESCALE_MASTER_TOKEN='<test-master-token>'
```

and to have valid `oc` tool session to Openshift where 3scale Operator is deployed and watches for CRs.

By default:
    - `oc` namespace should be the namespace where 3scale instance is deployed
    - the `system-seed` secret is used by 3scale Operator client
    - `THREESCALE_` variables are used for not implemented Threescale client features

If CRs are created in different namespace to 3scale deployment, env variable 
`OCP_PROVIDER_ACCOUNT_REF` can be specified with secret name used by 3scale Operator client,
see https://github.com/3scale/3scale-operator/blob/master/doc/backend-reference.md#provider-account-reference

### Finished integration unit tests

- AccountUsers
- Accounts
- ActiveDocs
- ApplicationPlans
- BackendMappingRules
- BackendMetrics
- BackendUsages
- Backends
- Limits
- MappingRules
- Metrics
- OpenApis
- Policies
- PolicyRegistries
- PricingRules
- Proxies
- Services
- Tenants
- ProxyConfigPromote
- Applications
- Methods
- ApplicationAuth

Command to run integration unit tests: `pipenv run pytest --log-cli-level=10 -vvvv -s ./tests/integration/ |& tee x`
 
### TODO
- do https://github.com/3scale/3scale-operator/pull/813
- do not simulate app plan id
- create unit integration tests for:
  - ProductDeploymentSpec
  - AuthenticationSpec
- implement delete of policies + add unit tests
- add proper error messages in case of for example missing required arguments, see test_should_fields_be_required 
- implement optimitazation on the oc level:
  - for every test run, label objects - oc label product.capabilities.3scale.net/testyrclkfzyhue test_run=new --overwrite
  - use only objects labeled by test run id - oc get product.capabilities.3scale.net --show-labels=true -l test_run=new
