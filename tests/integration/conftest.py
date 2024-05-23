import os
import secrets
import random
import string
from distutils.util import strtobool

import pytest
from dotenv import load_dotenv

# from threescale_api import errors

import threescale_api
import threescale_api_crd

from threescale_api_crd.resources import (
    Service,
    Metric,
    BackendUsage,
    BackendMappingRule,
    Backend,
    ActiveDoc,
    PolicyRegistry,
    MappingRule,
    Limit,
    ApplicationPlan,
    Proxy,
    PricingRule,
    Application,
)

load_dotenv()


def cleanup(resource):
    resource.delete()
    assert not resource.exists()


#    pass


def get_suffix() -> str:
    return secrets.token_urlsafe(8)


@pytest.fixture(scope="session")
def url() -> str:
    return os.getenv("THREESCALE_PROVIDER_URL")


@pytest.fixture(scope="session")
def token() -> str:
    return os.getenv("THREESCALE_PROVIDER_TOKEN")


@pytest.fixture(scope="session")
def master_url() -> str:
    return os.getenv("THREESCALE_MASTER_URL")


@pytest.fixture(scope="session")
def master_token() -> str:
    return os.getenv("THREESCALE_MASTER_TOKEN")


@pytest.fixture(scope="session")
def ssl_verify() -> bool:
    ssl_verify = os.getenv("THREESCALE_SSL_VERIFY", "false")
    ssl_verify = bool(strtobool(ssl_verify))
    if not ssl_verify:
        import urllib3

        urllib3.disable_warnings()
    return ssl_verify


@pytest.fixture(scope="session")
def api_backend() -> str:
    return os.getenv("TEST_API_BACKEND", "http://www.httpbin.org:80")


@pytest.fixture(scope="session")
def ocp_provider_ref() -> str:
    return os.getenv("OCP_PROVIDER_ACCOUNT_REF")


@pytest.fixture(scope="session")
def api(
    url: str, token: str, ssl_verify: bool, ocp_provider_ref: str
) -> threescale_api_crd.ThreeScaleClientCRD:
    return threescale_api_crd.ThreeScaleClientCRD(
        url=url, token=token, ssl_verify=ssl_verify, ocp_provider_ref=ocp_provider_ref
    )


@pytest.fixture(scope="session")
def api_origin(
    url: str, token: str, ssl_verify: bool, ocp_provider_ref: str
) -> threescale_api.ThreeScaleClient:
    return threescale_api.ThreeScaleClient(url=url, token=token, ssl_verify=ssl_verify)


@pytest.fixture(scope="session")
def master_api(
    master_url: str, master_token: str, ssl_verify: bool, ocp_provider_ref: str
) -> threescale_api_crd.ThreeScaleClientCRD:
    return threescale_api_crd.ThreeScaleClientCRD(
        url=master_url,
        token=master_token,
        ssl_verify=ssl_verify,
        ocp_provider_ref=ocp_provider_ref,
    )


@pytest.fixture(scope="module")
def apicast_http_client(application, proxy, ssl_verify):
    proxy.deploy()
    return application.api_client(verify=ssl_verify)


@pytest.fixture(scope="module")
def service_params():
    suffix = get_suffix()
    return {"name": f"test-{suffix}"}


@pytest.fixture(scope="module")
def service(service_params, api) -> Service:
    service = api.services.create(params=service_params)
    yield service
    cleanup(service)


@pytest.fixture(scope="module")
def account_params():
    suffix = get_suffix()
    name = f"testacc{suffix}"
    return {
        "name": name,
        "username": name,
        "org_name": name,
        "monthly_billing_enabled": False,
        "monthly_charging_enabled": False,
        "email": f"{name}@name.none",
    }


@pytest.fixture(scope="module")
def account(api, account_params):
    acc = api.accounts.create(params=account_params)
    account_params.update(account_name=acc["name"])
    yield acc
    cleanup(acc)


@pytest.fixture(scope="module")
def acc_user(account):
    return account.users.list()[-1]


@pytest.fixture(scope="module")
def acc_user2_params(account, acc_user):
    name = acc_user["username"] + "2"
    return {
        "username": name,
        "email": f"{name}@name.none",
        "role": "member",
        "account_name": account["name"],
    }


@pytest.fixture(scope="module")
def acc_user2(account, acc_user, acc_user2_params):
    return account.users.create(acc_user2_params)


@pytest.fixture(scope="module")
def application_plan_params(service) -> dict:
    suffix = get_suffix()
    return {
        "name": f"test-{suffix}",
        "setup_fee": "1.00",
        "state_event": "publish",
        "cost_per_month": "3.00",
    }


@pytest.fixture(scope="module")
def application_plan(api, service, application_plan_params) -> ApplicationPlan:
    resource = service.app_plans.create(params=application_plan_params)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def application_params(application_plan, service, account):
    suffix = get_suffix()
    name = f"test-{suffix}"
    return {
        "name": name,
        "description": name,
        "plan_id": application_plan["id"],
        "service_id": service["id"],
        "account_id": account["id"],
    }


@pytest.fixture(scope="module")
def application(service, application_plan, application_params, account) -> Application:
    resource = account.applications.create(params=application_params)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def app_key_params(account, application):
    value = "".join(
        random.choices(
            string.ascii_uppercase
            + string.digits
            + "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
            k=100,
        )
    )
    return {
        "application_id": application["id"],
        "account_id": account["id"],
        "key": value,
    }


@pytest.fixture(scope="module")
def app_key(application, app_key_params) -> threescale_api.resources.ApplicationKey:
    resource = application.keys.create(params=app_key_params)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def proxy(service) -> Proxy:
    return service.proxy.list()


@pytest.fixture(scope="module")
def backend_usage_params(service, backend):
    return {
        "service_id": service["id"],
        "backend_id": backend["id"],
        "path": "/",
    }


@pytest.fixture(scope="module")
def backend_updated_usage_params(backend_usage_params):
    ret = backend_usage_params.copy()
    ret["path"] = "/post"
    return ret


@pytest.fixture(scope="module")
def backend_usage(service, backend, backend_usage_params) -> BackendUsage:
    service = service.read()
    resource = service.backend_usages.create(params=backend_usage_params)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def metric_params(service):
    suffix = get_suffix()
    friendly_name = f"test-metric-{suffix}"
    name = f"{friendly_name}".replace("-", "_")
    return {"friendly_name": friendly_name, "system_name": name, "unit": "count"}


@pytest.fixture(scope="module")
def backend_metric_params():
    suffix = get_suffix()
    friendly_name = f"test-metric-{suffix}"
    name = f"{friendly_name}".replace("-", "")
    return {"friendly_name": friendly_name, "system_name": name, "unit": "count"}


@pytest.fixture(scope="module")
def updated_metric_params(metric_params):
    suffix = get_suffix()
    friendly_name = f"test-updated-metric-{suffix}"
    metric_params["friendly_name"] = f"/get/{friendly_name}"
    return metric_params


@pytest.fixture(scope="module")
def backend_updated_metric_params(backend_metric_params):
    updated = backend_metric_params.copy()
    suffix = get_suffix()
    friendly_name = f"test-updated-metric-{suffix}"
    updated["friendly_name"] = f"/get/{friendly_name}"
    return updated


@pytest.fixture(scope="module")
def metric(service, metric_params) -> Metric:
    resource = service.metrics.create(params=metric_params)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def method_params():
    suffix = get_suffix()
    friendly_name = f"test-method-{suffix}"
    system_name = f"{friendly_name}".replace("-", "_")
    return {"friendly_name": friendly_name, "system_name": system_name}


# 'friendly_name' is id in CRD for methods
@pytest.fixture(scope="module")
def updated_method_params(method_params):
    suffix = get_suffix()
    description = f"test-updated-method-{suffix}"
    method_params["description"] = description
    return method_params


@pytest.fixture(scope="module")
def method(hits_metric, method_params):
    resource = hits_metric.methods.create(params=method_params)
    yield resource
    cleanup(resource)
    # service.proxy.deploy()


@pytest.fixture(scope="module")
def hits_metric(service):
    return service.metrics.read_by(system_name="hits")


def get_mapping_rule_pattern():
    suffix = get_suffix()
    pattern = f"test-{suffix}".replace("_", "-")
    return pattern


@pytest.fixture(scope="module")
def mapping_rule_params(service):
    """
    Fixture for getting paramteres for mapping rule for product/service.
    """
    hits_metric = service.metrics.read_by_name("hits")
    return {
        "http_method": "GET",
        "pattern": "/get",
        "metric_id": hits_metric["id"],
        "delta": 1,
    }


@pytest.fixture(scope="module")
def backend_mapping_rule_params(backend, backend_metric):
    """
    Fixture for getting paramteres for mapping rule for backend.
    """
    back = backend_metric["id"]
    return {
        "http_method": "GET",
        "pattern": "/anything/get/ida",
        "metric_id": back,
        "delta": 1,
    }


@pytest.fixture(scope="module")
def updated_mapping_rules_params(mapping_rule_params):
    """
    Fixture for updating mapping rule for product/service.
    """
    pattern = get_mapping_rule_pattern()
    params = mapping_rule_params.copy()
    params["pattern"] = f"/anything/get/{pattern}"
    return params


@pytest.fixture(scope="module")
def updated_backend_mapping_rules_params(backend_mapping_rule_params):
    """
    Fixture for updating mapping rule for backend.
    """
    pattern = get_mapping_rule_pattern()
    params = backend_mapping_rule_params.copy()
    params["pattern"] = f"/anything/get/{pattern}"
    return params


@pytest.fixture(scope="module")
def mapping_rule(service, mapping_rule_params, proxy) -> MappingRule:
    """
    Fixture for getting mapping rule for product/service.
    """
    resource = service.mapping_rules.create(params=mapping_rule_params)
    yield resource
    cleanup(resource)
    proxy.deploy()


@pytest.fixture(scope="module")
def backend_mapping_rule(
    backend, backend_metric, backend_mapping_rule_params, service, proxy, backend_usage
) -> BackendMappingRule:
    """
    Fixture for getting mapping rule for backend.
    """
    backend = backend.read()
    resource = backend.mapping_rules.create(params=backend_mapping_rule_params)
    yield resource
    cleanup(resource)
    proxy.deploy()


@pytest.fixture(scope="module")
def create_mapping_rule(service):
    """
    Fixture for creating mapping rule for product/service.
    """
    rules = []

    def _create(metric, http_method, path):
        params = {
            "service_id": service["id"],
            "http_method": http_method,
            "pattern": f"/anything{path}",
            "delta": 1,
            "metric_id": metric["id"],
        }
        rule = service.mapping_rules.create(params=params)
        rules.append(rule)
        return rule

    yield _create

    # TODO
    # for rule in rules:
    #     if rule.exists():
    #         cleanup(rule)


@pytest.fixture(scope="module")
def create_backend_mapping_rule(backend):
    """
    Fixture for creating mapping rule for backend.
    """
    rules = []

    def _create(backend_metric, http_method, path):
        params = {
            "backend_id": backend["id"],
            "http_method": http_method,
            "pattern": f"/anything{path}",
            "delta": 1,
            "metric_id": backend_metric["id"],
        }
        rule = backend.mapping_rules.create(params=params)
        rules.append(rule)
        return rule

    yield _create

    for rule in rules:
        if rule.exists():
            cleanup(rule)


@pytest.fixture(scope="module")
def backend_params(api_backend):
    """
    Fixture for getting backend parameters.
    """
    suffix = get_suffix()
    return {
        "name": f"test-backend-{suffix}",
        "private_endpoint": api_backend,
        "description": "111",
    }


@pytest.fixture(scope="module")
def backend(backend_params, api) -> Backend:
    """
    Fixture for getting backend.
    """
    backend = api.backends.create(params=backend_params)
    yield backend
    cleanup(backend)


@pytest.fixture(scope="module")
def backend_metric(backend, backend_metric_params) -> Metric:
    """
    Fixture for getting backend metric.
    """
    resource = backend.metrics.create(params=backend_metric_params)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def custom_tenant(master_api, tenant_params):
    """
    Fixture for getting the custom tenant.
    """
    resource = master_api.tenants.create(tenant_params)
    yield resource
    resource.delete()


@pytest.fixture(scope="module")
def tenant_params():
    """
    Params for custom tenant
    """
    return {
        "username": f"tenant{get_suffix()}",
        "admin_password": "123456",
        "email": f"e{get_suffix()}@invalid.invalid",
        "org_name": "org",
    }


@pytest.fixture(scope="module")
def active_docs_body():
    return """{"openapi":"3.0.0","info":{"version":"1.0.0","title":"example"},"paths":{
            "/pets":{"get":{"summary":"List all pets","operationId":"listPets","responses":
            {"200":{"description":"A paged array of pets"}}}}},"components":{}}"""


@pytest.fixture(scope="module")
def active_docs_params(active_docs_body):
    suffix = get_suffix()
    name = f"test-{suffix}"
    des = f"description-{suffix}"
    return {"name": name, "body": active_docs_body, "description": des}


@pytest.fixture(scope="module")
def active_doc(api, service, active_docs_params) -> ActiveDoc:
    """
    Fixture for getting active doc.
    """
    acs = active_docs_params.copy()
    acs["service_id"] = service["id"]
    resource = api.active_docs.create(params=acs)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def openapi_params(active_docs_body):
    suffix = get_suffix()
    name = f"test-{suffix}"
    params = {
        "name": name,
        "productionPublicBaseURL": "http://productionPublicBaseURL",
        "stagingPublicBaseURL": "http://stagingPublicBaseURL",
        "productSystemName": "PrOdUcTsYsTeMnAmE",
        "privateBaseURL": "http://privateBaseURL",
        "prefixMatching": True,
        "privateAPIHostHeader": "privateAPIHostHeader",
        "privateAPISecretToken": "privateAPISecretToken",
        "body": active_docs_body,
    }
    return params


@pytest.fixture(scope="module")
def openapi(api, openapi_params):
    """
    Fixture for getting OpenApi.
    """
    resource = api.openapis.create(params=openapi_params.copy())
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def webhook(api):
    return api.webhooks


@pytest.fixture(scope="session")
def policy_registry_schema():
    return {
        "summary": "This is just an example.",
        "description": [
            "This policy is just an example\
            how to write your custom policy.\nAnd this is next line",
            "And next item.",
        ],
        "name": "APIcast Example Policy",
        "$schema": "http://apicast.io/policy-v1/schema#manifest#",
        "version": "0.1",
        "configuration": {
            "properties": {
                "property1": {
                    "description": "list of properties1",
                    "items": {
                        "properties": {
                            "value1": {"description": "Value1", "type": "string"},
                            "value2": {"description": "Value2", "type": "string"},
                        },
                        "required": ["value1"],
                        "type": "object",
                    },
                    "type": "array",
                }
            },
            "type": "object",
        },
    }


@pytest.fixture(scope="module")
def policy_registry_params(policy_registry_schema):
    """Params for policy registry."""
    suffix = get_suffix()
    name = f"test-{suffix}"
    return {"name": name, "version": "0.1", "schema": policy_registry_schema}


@pytest.fixture(scope="module")
def policy_registry(api, policy_registry_params) -> PolicyRegistry:
    """
    Fixture for getting policy registry.
    """
    acs = policy_registry_params.copy()
    resource = api.policy_registry.create(params=acs)
    yield resource
    cleanup(resource)


@pytest.fixture(scope="module")
def limit_params(metric):
    """Params for limit."""
    return {"metric_id": metric["id"], "period": "minute", "value": 10}


@pytest.fixture(scope="module")
def limit(service, application, application_plan, metric, limit_params) -> Limit:
    """
    Fixture for getting limit.
    """
    resource = application_plan.limits(metric).create(limit_params)
    yield resource
    resource.delete()


@pytest.fixture(scope="module")
def backend_limit_params(backend_metric):
    """Params for limit."""
    return {"metric_id": backend_metric["id"], "period": "minute", "value": 10}


@pytest.fixture(scope="module")
def backend_limit(
    service,
    application,
    application_plan,
    backend_metric,
    backend_limit_params,
    backend_usage,
) -> Limit:
    """
    Fixture for getting limit for backend metric.
    """
    resource = application_plan.limits(backend_metric).create(backend_limit_params)
    yield resource
    resource.delete()


@pytest.fixture(scope="module")
def prule_params(metric):
    """Params for prule."""
    return {"metric_id": metric["id"], "min": 10, "max": 100, "cost_per_unit": "10"}


@pytest.fixture(scope="module")
def prule(service, application, application_plan, metric, prule_params) -> PricingRule:
    """
    Fixture for getting prule.
    """
    resource = application_plan.pricing_rules(metric).create(prule_params)
    yield resource
    resource.delete()


@pytest.fixture(scope="module")
def backend_prule_params(backend_metric):
    """Params for prule."""
    return {
        "metric_id": backend_metric["id"],
        "min": 10,
        "max": 100,
        "cost_per_unit": 10,
    }


@pytest.fixture(scope="module")
def backend_prule(
    service,
    application,
    application_plan,
    backend_metric,
    backend_prule_params,
    backend_usage,
) -> PricingRule:
    """
    Fixture for getting prule for backend metric.
    """
    resource = application_plan.pricing_rules(backend_metric).create(
        backend_prule_params
    )
    yield resource
    resource.delete()


@pytest.fixture(scope="module")
def promote_params(api, service):
    """
    Promote params for service.
    """
    return {"productCRName": service.crd.as_dict()["metadata"]["name"]}


@pytest.fixture(scope="module")
def promote(api, service, backend, backend_usage, promote_params):
    """
    Promote object for service.
    """
    resource = api.promotes.create(params=promote_params)
    yield resource
    cleanup(resource)
