import secrets
import random
import string
import pytest

from tests.integration import asserts


# tests important for CRD - CRU + list
def test_application_list_global(api, application):
    applications = api.applications.list()
    assert len(applications) >= 1


def test_application_list(account, application):
    applications = account.applications.list()
    assert len(applications) >= 1


def test_application_can_be_created(application_params, application):
    asserts.assert_resource(application)
    asserts.assert_resource_params(application, application_params)


def test_application_can_be_read(api, application_params, application):
    read = api.applications.read(int(application.entity_id))
    asserts.assert_resource(read)
    asserts.assert_resource_params(read, application_params)


def test_application_can_be_read_by_name(api, application_params, application):
    app_name = application["name"]
    read = api.applications[app_name]
    asserts.assert_resource(read)
    asserts.assert_resource_params(read, application_params)


@pytest.fixture(scope="module")
def application_plan_params2():
    suffix = secrets.token_urlsafe(8)
    return {
        "name": f"test-{suffix}",
        "setup_fee": "1.00",
        "state_event": "publish",
        "cost_per_month": "3.00",
    }


@pytest.fixture(scope="module")
def application_plan2(service, application_plan_params2):
    resource = service.app_plans.create(params=application_plan_params2)
    yield resource
    resource.delete()


@pytest.fixture(scope="module")
def update_application_params(application_plan2):
    suffix = secrets.token_urlsafe(8)
    name = f"updated-{suffix}"
    return {"name": name, "description": name, "plan_id": application_plan2["id"]}


def test_application_update(update_application_params, application):
    updated_application = application.update(params=update_application_params)
    asserts.assert_resource(updated_application)
    asserts.assert_resource_params(updated_application, update_application_params)


# tests important for CRD - CRU + list

# changing application state tests


def test_application_set_state(application):
    application = application.set_state("suspend")
    assert application["state"] == "suspended"
    application = application.set_state("resume")
    assert application["state"] == "live"


# Application Atuhentication - Application keys


def test_application_key_list(application, app_key):
    keys = application.keys.list()
    assert len(keys) > 0


def test_application_key_can_be_created(app_key, app_key_params):
    asserts.assert_resource(app_key)
    asserts.assert_resource_params(app_key, app_key_params)


def test_application_autogenerated_key_can_be_created(application, app_key_params):
    keys_len = len(application.keys.list())
    key_params = app_key_params.copy()
    key_params.pop("key", None)
    key_params["generateSecret"] = True
    new_key = application.keys.create(params=key_params)
    asserts.assert_resource(new_key)
    asserts.assert_resource_params(new_key, key_params)
    assert new_key["value"]
    assert len(application.keys.list()) == keys_len + 1


def test_application_update_userkey(application):
    new_key = "".join(
        random.choices(string.ascii_letters + string.digits + "-_.", k=100)
    )
    application.update(params={"user_key": new_key})
    application.read()
    asserts.assert_resource(application)
    assert application["user_key"] == new_key
