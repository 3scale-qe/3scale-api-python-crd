"""Module with default objects"""

import logging
import copy
import random
import string
import time
from typing import Dict, List, Union

import threescale_api
import threescale_api.errors
import openshift_client as ocp

LOG = logging.getLogger(__name__)


class DefaultClientCRD(threescale_api.defaults.DefaultClient):
    """Default CRD client."""

    CRD_IMPLEMENTED = False
    SPEC = None
    SELECTOR = None
    KEYS = None
    ID_NAME = None

    def __init__(
        self, parent=None, instance_klass=None, entity_name=None, entity_collection=None
    ):
        ocp.set_default_loglevel(6)
        super().__init__(
            parent=parent,
            instance_klass=instance_klass,
            entity_name=entity_name,
            entity_collection=entity_collection,
        )
        ocp.set_default_project(self.threescale_client.ocp_namespace)

    def get_list(self, typ="normal"):
        """Returns list of entities."""
        return []

    def get_selector(self, obj_name=None):
        """Returns OCP selector for objects."""
        sel = self.SELECTOR + ".capabilities.3scale.net"
        if obj_name:
            sel += "/" + obj_name
        return ocp.selector(sel)

    def read_crd(self, obj_name=None):
        """Read current CRD definition based on selector and/or object name."""
        LOG.info("CRD read %s %s", str(self.SELECTOR), str(obj_name))
        return self.get_selector(obj_name).objects()

    def is_crd_implemented(self):
        """Returns True is crd is implemented in the client"""
        return self.__class__.CRD_IMPLEMENTED

    def enable_crd_implemented(self):
        """Set True to crd is implemented attribute"""
        self.__class__.CRD_IMPLEMENTED = True

    def disable_crd_implemented(self):
        """Set False to crd is implemented attribute"""
        self.__class__.CRD_IMPLEMENTED = False

    def fetch_crd_entity(self, name: str):
        """Fetches the entity based on crd name
        Args:
            name(str): entity crd name
        Returns(obj): Resource
        """
        LOG.info(self._log_message("[FETCH] CRD Fetch by crd name: ", entity_id=name))
        if not self.is_crd_implemented():
            raise threescale_api.errors.ThreeScaleApiError(
                message="Not supported method"
            )
        inst = self._create_instance(response=self.read_crd(name))
        return inst[0] if inst else None

    def read_by_name(self, name: str, **kwargs) -> "DefaultResourceCRD":
        """Read resource by name
        Args:
            name: Name of the resource (either system name, name, org_name ...)
            **kwargs:

        Returns:

        """
        return self.fetch_crd_entity(name) or super().read_by_name(name, **kwargs)

    def read(self, entity_id: int = None, **kwargs) -> "DefaultResourceCRD":
        """Read the instance, read will just create empty resource and lazyloads only if needed
        Args:
            entity_id(int): Entity id
        Returns(DefaultResourceCRD): Default resource
        """
        LOG.debug(self._log_message("[READ] CRD Read ", entity_id=entity_id))
        if self.is_crd_implemented():
            return self.fetch(entity_id=entity_id, **kwargs)
        else:
            return threescale_api.defaults.DefaultClient.read(self, entity_id, **kwargs)

    def fetch(self, entity_id: int = None, **kwargs):
        """Fetches the entity dictionary
        Args:
            entity_id(int): Entity id
            **kwargs: Optional args

        Returns(dict): Resource dict from the 3scale
        """
        LOG.info(
            self._log_message("[FETCH] CRD Fetch ", entity_id=entity_id, args=kwargs)
        )
        if self.is_crd_implemented():
            list_crds = self.read_crd()
            instance_list = self._create_instance(response=list_crds)
            ret = []
            if isinstance(instance_list, list):
                ret = (
                    [
                        instance
                        for instance in instance_list
                        if (instance.entity_id and instance.entity_id == entity_id)
                        or entity_id is None
                    ][:1]
                    or [None]
                )[0]
            else:
                # proxy.fetch exception
                ret = instance_list
            return ret
        return threescale_api.defaults.DefaultClient.fetch(self, entity_id, **kwargs)

    def exists(self, entity_id=None, **kwargs) -> bool:
        """Check whether the resource exists
        Args:
            entity_id(int): Entity id
            **kwargs: Optional args

        Returns(bool): True if the resource exists
        """
        LOG.info(
            self._log_message(
                "[EXIST] CRD Resource exist ", entity_id=entity_id, args=kwargs
            )
        )
        return self.fetch(entity_id, **kwargs)

    def _list(self, **kwargs) -> list["DefaultResourceCRD"]:
        """Internal list implementation used in list or `select` methods
        Args:
            **kwargs: Optional parameters

        Returns(List['DefaultResourceCRD']):

        """
        LOG.info(self._log_message("[_LIST] CRD", args=kwargs))
        if self.is_crd_implemented():
            list_crds = self.read_crd()
            instance = self._create_instance(response=list_crds, collection=True)
            return instance
        return threescale_api.defaults.DefaultClient._list(self, **kwargs)

    @staticmethod
    def normalize(str_in: str):
        """Some values in CRD cannot contain some characters."""
        return str_in.translate(
            "".maketrans({"-": "", "_": "", "/": "", "[": "", "]": ""})
        ).lower()

    @staticmethod
    def cleanup_spec(spec, keys, params):
        """Removes from spec attributes with None value."""
        for key, value in keys.items():
            if (
                params.get(key, None) is None
                and value in spec["spec"]
                and spec["spec"][value] is None
            ):
                del spec["spec"][value]

    def create(self, params: dict = None, **kwargs) -> "DefaultResourceCRD":
        LOG.info(self._log_message("[CREATE] Create CRD ", body=params, args=kwargs))
        if self.is_crd_implemented():
            spec = copy.deepcopy(self.SPEC)
            name = params.get("name") or params.get(
                "username"
            )  # Developer User exception
            if name is not None:
                name = self.normalize(name)
                if params.get("name"):
                    params["name"] = name
                else:
                    params["username"] = name
            else:
                name = self.normalize(
                    "".join(random.choice(string.ascii_letters) for _ in range(16))
                )

            spec["metadata"]["namespace"] = self.threescale_client.ocp_namespace
            spec["metadata"]["name"] = name
            spec = self._set_provider_ref_new_crd(spec)
            self.before_create(params, spec)

            spec["spec"].update(self.translate_to_crd(params))
            DefaultClientCRD.cleanup_spec(spec, self.KEYS, params)

            result = ocp.create(spec)
            assert result.status() == 0
            # list_objs = self.read_crd(result.out().strip().split('/')[1])
            created_objects = []
            # counters = [89, 55, 34, 21, 13, 8, 5, 3, 2, 1, 1, 1]
            # while len(list_objs) > 0 and len(counters) > 0:
            #    list_objs2 = []
            #    for obj in list_objs:
            #        obj.refresh()
            #        status = obj.as_dict().get('status', None)
            #        if status:
            #            new_id = status.get(self.ID_NAME, 0)
            #            if self._is_ready(status, new_id):
            #                created_objects.append(obj)
            #            else:
            #                list_objs2.append(obj)
            #        else:
            #            list_objs2.append(obj)
            #    list_objs = list_objs2
            #    if not list_objs:
            #        time.sleep(counters.pop())

            timeout = 1000
            # if self.__class__.__name__ in ['Promotes']:
            #    timeout = 1000

            with ocp.timeout(timeout):
                success, created_objects, _ = result.until_all(
                    success_func=lambda obj: self._is_ready(obj)
                )
                assert created_objects
                assert success

            instance = (self._create_instance(response=created_objects)[:1] or [None])[
                0
            ]
            return instance

        return threescale_api.defaults.DefaultClient.create(self, params, **kwargs)

    def _set_provider_ref_new_crd(self, spec):
        """set provider reference to new crd"""
        if self.threescale_client.ocp_provider_ref is None:
            spec["spec"].pop("providerAccountRef")
        else:
            spec["spec"]["providerAccountRef"][
                "name"
            ] = self.threescale_client.ocp_provider_ref
            spec["spec"]["providerAccountRef"][
                "namespace"
            ] = self.threescale_client.ocp_namespace
        return spec

    def _is_ready(self, obj):
        """Is object ready?"""
        if not ("status" in obj.model and "conditions" in obj.model.status):
            return False
        status = obj.as_dict()["status"]
        new_id = status.get(self.ID_NAME, 0)
        state = {"Failed": True, "Invalid": True, "Synced": False, "Ready": False}
        for sta in status["conditions"]:
            state[sta["type"]] = sta["status"] == "True"

        return (
            not state["Failed"]
            and not state["Invalid"]
            and (state["Synced"] or state["Ready"])
            and (new_id != 0)
        )

    def _create_instance(self, response, klass=None, collection: bool = False):
        klass = klass or self._instance_klass
        if self.is_crd_implemented():
            extracted = self._extract_resource_crd(response, collection, klass=klass)
            instance = self._instantiate_crd(extracted=extracted, klass=klass)
        else:
            extracted = self._extract_resource(response, collection)
            instance = self._instantiate(extracted=extracted, klass=klass)
        LOG.info("[INSTANCE] CRD Created instance: %s", str(instance))
        return instance

    def _extract_resource_crd(self, response, collection, klass):
        extract_params = {"response": response, "entity": self._entity_name}
        if collection:
            extract_params["collection"] = self._entity_collection
        extracted = None
        if isinstance(response, list):
            if response:
                return [{"spec": obj.as_dict()["spec"], "crd": obj} for obj in response]
            return None

        return extracted

    def _instantiate_crd(self, extracted, klass):
        if isinstance(extracted, list):
            instance = [self.__make_instance_crd(item, klass) for item in extracted]
            return self._create_instance_trans(instance)
        if extracted:
            return self.__make_instance_crd(extracted, klass)
        return None

    def _create_instance_trans(self, instance):
        return instance

    def __make_instance_crd(self, extracted: dict, klass):
        instance = (
            klass(client=self, spec=extracted["spec"], crd=extracted["crd"])
            if klass
            else extracted
        )
        return instance

    def delete(
        self, entity_id: int = None, resource: "DefaultResourceCRD" = None, **kwargs
    ) -> bool:
        """Method deletes resource."""
        LOG.info(
            self._log_message("[DELETE] Delete CRD ", entity_id=entity_id, args=kwargs)
        )
        if self.is_crd_implemented():
            resource.crd.delete()
            return True
        return threescale_api.defaults.DefaultClient.delete(
            self, entity_id=entity_id, **kwargs
        )

    def update(
        self,
        entity_id=None,
        params: dict = None,
        resource: "DefaultResourceCRD" = None,
        **kwargs
    ) -> "DefaultResourceCRD":
        LOG.info(
            self._log_message(
                "[UPDATE] Update CRD", body=params, entity_id=entity_id, args=kwargs
            )
        )
        new_params = {}
        if resource:
            new_params = {**resource.entity}
        if params:
            new_params.update(params)
        # TODO change ids for objects which require ids
        if self.is_crd_implemented():
            new_params = copy.deepcopy(new_params)
            self.before_update(new_params, resource)
            new_spec = self.translate_to_crd(new_params)
            if resource.crd is None:
                resource = resource.read()
                if isinstance(resource, list):
                    resource = resource[0]
            else:
                resource.crd.refresh()
            new_crd = resource.crd.as_dict()
            new_crd["spec"].update(new_spec)
            if self.__class__.__name__ not in ["Tenants"]:
                if self.threescale_client.ocp_provider_ref is None:
                    new_crd["spec"].pop("providerAccountRef", None)
                else:
                    new_crd["spec"]["providerAccountRef"] = {
                        "name": self.threescale_client.ocp_provider_ref,
                        # 'namespace': self.threescale_client.ocp_namespace
                    }
            resource.crd.model = ocp.Model(new_crd)
            result = resource.crd.replace()

            if result.status():
                LOG.error("[INSTANCE] Update CRD failed: %s", str(result))
                raise Exception(str(result))
            # return self.read(resource.entity_id)
            return resource

        return threescale_api.defaults.DefaultClient.update(
            self, entity_id=entity_id, params=params, **kwargs
        )

    def trans_item(self, key, value, obj):
        """Transform one attribute in CRD spec."""
        return obj[key]

    def translate_to_crd(self, obj):
        """Translate object attributes into object ready for merging into CRD."""
        map_ret = {}

        for key, value in self.KEYS.items():
            LOG.debug("%s, %s, %s, %s", str(key), str(value), str(obj), str(type(obj)))
            if obj.get(key, None) is not None:
                set_value = self.trans_item(key, value, obj)
                if set_value is not None:
                    map_ret[value] = set_value

        return map_ret


class DefaultClientNestedCRD(DefaultClientCRD):
    """Default CRD client for nested objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_id_from_crd(self):
        """Returns object id extracted from CRD."""
        return None

    # flake8: noqa C901
    def _extract_resource_crd(self, response, collection, klass) -> list | dict:
        extract_params = {"response": response, "entity": self._entity_name}
        if collection:
            extract_params["collection"] = self._entity_collection
        extracted = None
        if isinstance(response, list):
            if self.is_crd_implemented():
                parent_id = int(self.topmost_parent().entity_id)
                service_with_maps = {}
                for prod in response:
                    prod_dict = prod.as_dict()
                    if prod_dict is None:
                        prod_dict = {}
                    idp = int(
                        prod_dict.get("status", {}).get(
                            self.topmost_parent().client.ID_NAME, 0
                        )
                    )
                    if idp == parent_id:
                        service_with_maps = prod
                        break
                spec = {}
                if service_with_maps != {}:
                    spec = (
                        DictQuery(service_with_maps.as_dict()).get(
                            klass.GET_PATH or self.get_path()
                        )
                    ) or []
                if isinstance(spec, list):
                    return [{"spec": obj, "crd": service_with_maps} for obj in spec]
                elif (
                    "apicastHosted" not in spec.keys()
                ):  # dict branch, exception for Proxy
                    ret = []
                    for key, obj in spec.items():
                        obj[self.ID_NAME] = key

                        ret.append({"spec": obj, "crd": service_with_maps})
                    return ret
                else:
                    return [{"spec": spec, "crd": service_with_maps}]

        return extracted

    def create(self, params: dict = None, **kwargs) -> "DefaultResourceCRD":
        LOG.info(
            self._log_message("[CREATE] Create CRD Nested ", body=params, args=kwargs)
        )
        if self.is_crd_implemented():
            spec = copy.deepcopy(self.SPEC)
            name = params.get("name") or params.get(
                "username"
            )  # Developer User exception
            if name is not None:
                name = self.normalize(name)
                if params.get("name"):
                    params["name"] = name
                else:
                    params["username"] = name
            else:
                params["name"] = self.normalize(
                    "".join(random.choice(string.ascii_letters) for _ in range(16))
                )
                name = params["name"]

            self.before_create(params, spec)

            spec["spec"].update(self.translate_to_crd(params))
            DefaultClientCRD.cleanup_spec(spec, self.KEYS, params)

            return self.in_create(self.get_list_from_spec(), params, spec)

        return threescale_api.defaults.DefaultClient.create(self, params, **kwargs)

    def delete(
        self, entity_id: int = None, resource: "DefaultResourceCRD" = None, **kwargs
    ) -> bool:
        """Method deletes resource."""
        LOG.info(
            self._log_message(
                "[DELETE] Delete CRD Nested ", entity_id=entity_id, args=kwargs
            )
        )
        if self.is_crd_implemented():
            spec = self.translate_to_crd(resource.entity)
            maps = self.remove_from_list(spec)
            self.update_list(maps)
            return True
        return threescale_api.defaults.DefaultClient.delete(
            self, entity_id=entity_id, **kwargs
        )

    def update(
        self,
        entity_id=None,
        params: dict = None,
        resource: "DefaultResourceCRD" = None,
        **kwargs
    ) -> "DefaultResourceCRD":
        LOG.info(
            self._log_message(
                "[UPDATE] Update CRD", body=params, entity_id=entity_id, args=kwargs
            )
        )
        new_params = {}
        if resource:
            new_params = {**resource.entity}
        if params:
            new_params.update(params)
        # TODO change ids for objects which require ids
        if self.is_crd_implemented():
            # ApplicationPlans
            # BackendMappingRules
            # BackendMetrics
            # BackendUsages
            # Limits
            # MappingRules
            # Metrics
            # Policies
            # PricingRules
            # Proxies
            # if self.__class__.__name__ == 'BackendUsages':
            spec = self.before_update(new_params, resource)

            maps = self.remove_from_list(spec)

            # par = self.parent
            maps = self.before_update_list(maps, new_params, spec, resource)

            par = self.update_list(maps)
            maps = self.get_list()
            return self.after_update_list(maps, par, new_params)

        return threescale_api.defaults.DefaultClient.update(
            self, entity_id=entity_id, params=params, **kwargs
        )

    def after_update_list(self, maps, par, new_params):
        """Returns updated list."""
        checked_keys = [key for key in new_params.keys() if key not in ["id"]]
        for mapi in maps:
            if all([new_params[key] == mapi[key] for key in checked_keys]):
                return mapi
        return None


class DefaultResourceCRD(threescale_api.defaults.DefaultResource):
    """Default CRD resource."""

    GET_PATH = None

    def __init__(self, *args, crd=None, **kwargs):
        super().__init__(**kwargs)
        self._crd = crd

    @property
    def crd(self):
        """CRD object property."""
        if not self._crd:
            self.read()
        return self._crd or self.entity.get("crd", None)

    @crd.setter
    def crd(self, value):
        self._crd = value

    @property
    def entity_id(self) -> int:
        return self._entity_id or self._entity.get("id") or self.get_id_from_crd()

    @entity_id.setter
    def entity_id(self, value):
        self._entity_id = value

    def get_id_from_crd(self):
        """Returns object id extracted from CRD."""
        counter = 5
        while counter > 0:
            self.crd = self.crd.refresh()
            status = self.crd.as_dict()["status"]
            ret_id = status.get(self.client.ID_NAME, None)
            if ret_id:
                return ret_id
            time.sleep(20)
            counter -= 1

        return None

    def get_path(self):
        """
        This function is usefull only for Limits and PricingRules and\
        it should be redefined there.
        """
        return self.__class__.GET_PATH


class DictQuery(dict):
    """Get value from nested dictionary."""

    def get(self, path, default=None):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [v.get(key, default) if v else None for v in list(val)]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break

        return val
