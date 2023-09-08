""" Module with resources for CRD for Threescale client """

import logging
import copy
import json
import base64
import string
import os
import secrets
import random
import yaml
import requests
import openshift as ocp

import threescale_api
import threescale_api.resources
from threescale_api_crd.defaults import DefaultClientCRD, DefaultResourceCRD, DefaultClientNestedCRD
from threescale_api_crd import constants

LOG = logging.getLogger(__name__)


class Services(DefaultClientCRD, threescale_api.resources.Services):
    """
    CRD client for Services.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_SERVICE
    KEYS = constants.KEYS_SERVICE
    SELECTOR = 'Product'
    ID_NAME = 'productId'

    def __init__(self, parent, *args, entity_name='service',
                 entity_collection='services', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'mapping_rules' in params.keys():
            spec['spec']['mappingRules'] = params['mapping_rules']
        if 'backend_version' in params.keys():
            spec['spec']['deployment']['apicastHosted']['authentication'] = constants.SERVICE_AUTH_DEFS[params['backend_version']]

    def before_update(self, new_params, resource):
        """Called before update."""
        if 'backend_version' in new_params.keys():
            resource.entity['deployment']['apicastHosted']['authentication'] = constants.SERVICE_AUTH_DEFS[new_params['backend_version']]

    @property
    def metrics(self) -> 'Metrics':
        """Returns metrics related to service/product."""
        return Metrics(parent=self, instance_klass=Metric)


class Proxies(DefaultClientNestedCRD, threescale_api.resources.Proxies):
    """
    CRD client for Proxies.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_PROXY
    KEYS = constants.KEYS_PROXY
    SELECTOR = 'Product'
    ID_NAME = 'name'

    def __init__(self, parent, *args, entity_name='proxy', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params['id'] = resource.parent.entity_id
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        return self.translate_to_crd(new_params)

    def get_list(self, typ=None):
        """ Returns list of entities. """
        return []

    def get_list_from_spec(self):
        """ Returns list from spec """
        return []

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        obj = {}
        iter_obj = obj
        # service.proxy.oidc.update(params={"oidc_configuration": DEFAULT_FLOWS})

        for path in resource.spec_path:
            if path not in iter_obj:
                if path == resource.spec_path[-1]:
                    iter_obj[path] = spec
                    if resource.oidc['oidc_configuration']:
                        auth_flow = self.translate_specific_to_crd(
                                resource.oidc['oidc_configuration'],
                                constants.KEYS_OIDC)
                        iter_obj[path]['authenticationFlow'] = auth_flow
                    if resource.responses or\
                        (set(new_params.keys()).intersection(set(constants.KEYS_PROXY_RESPONSES))):
                        resource.responses = True
                        resps = self.translate_specific_to_crd(new_params, constants.KEYS_PROXY_RESPONSES)
                        iter_obj[path]['gatewayResponse'] = resps
                    if resource.security:
                        sec = self.translate_specific_to_crd(new_params, constants.KEYS_PROXY_SECURITY)
                        iter_obj[path]['gatewayResponse'] = sec

                else:
                    iter_obj[path] = {}
            iter_obj = iter_obj[path]

        maps = obj

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'deployment': maps})

    def after_update_list(self, maps, par, new_params):
        """ Returns updated list. """
        return par.proxy.list()

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent

    def list(self, **kwargs):
        return DefaultClientCRD.list(self, **kwargs)

    def delete(self):
        """This functions is not implemented for Proxies."""
        raise threescale_api.ThreeScaleApiError("Delete not implemented for Proxies")

    def deploy(self):
        """
        Promotes proxy to staging.
        """
        return self.list().deploy()

    @property
    def oidc(self) -> 'OIDCConfigs':
        return OIDCConfigs(self)

    def translate_specific_to_crd(self, obj, keys):
        """ Translate Proxy attributes to CRD. """
        map_ret = {}
        trans_item = lambda key, value, obj: obj[key]
        for key, value in keys.items():
            LOG.debug('%s, %s, %s, %s', key, value, obj, type(obj))
            if obj.get(key, None) is not None:
                set_value = trans_item(key, value, obj)
                if set_value is not None:
                    map_ret[value] = set_value
        return map_ret

    def _create_instance_trans(self, instance):
        return instance[0]

    def remove_from_list(self, proxies_list, spec):
        """Return empty list because this function is not valid for Proxies.:"""
        return []


class Backends(DefaultClientCRD, threescale_api.resources.Backends):
    """
    CRD client for Backends.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_BACKEND
    KEYS = constants.KEYS_BACKEND
    SELECTOR = 'Backend'
    ID_NAME = 'backendId'

    def __init__(self, parent, *args, entity_name='backend_api',
                 entity_collection='backend_apis', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'mapping_rules' in params.keys():
            spec['mappingRules'] = params['mapping_rules']

    def before_update(self, new_params, resource):
        """Called before update."""

    @property
    def metrics(self) -> 'BackendMetrics':
        """ Returns metrics related to this backend. """
        return BackendMetrics(parent=self, instance_klass=BackendMetric)


class MappingRules(DefaultClientNestedCRD, threescale_api.resources.MappingRules):
    """
    CRD client for MappingRules.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_MAPPING_RULE
    KEYS = constants.KEYS_MAPPING_RULE
    SELECTOR = 'Product'
    ID_NAME = 'name'

    def __init__(self, parent, *args, entity_name='mapping_rule',
                 entity_collection='mapping_rules', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'last' in params.keys() and isinstance(params['last'], str):
            params.update({'last': params['last'] == "true"})

    def in_create(self, maps, params, spec):
        """Do steps to create new instance"""
        if 'metric_id' not in params.keys():
            spec['spec']['metricMethodRef'] = 'hits'
        elif isinstance(params['metric_id'], int):
            met = self.parent.metrics.read(int(params['metric_id']))
            # exception because of backend mapping rules
            name = met.entity.get('system_name', met.entity.get('name'))
            if '.' in met['system_name']:
                spec['spec']['metricMethodRef'] = name.split('.')[0]
            spec['spec']['metricMethodRef'] = name
        else:
            # metric id is tuple
            spec['spec']['metricMethodRef'] = params['metric_id'][0]
        MappingRules.insert_into_position(maps, params, spec)
        self.parent.update({'mapping_rules': maps})
        maps = self.list()
        return MappingRules.get_from_position(maps, params)

    def get_list(self, typ=None):
        """ Returns list of entities. """
        return self.parent.mapping_rules.list()

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec'].get('mapping_rules', [])

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params['id'] = (new_params['http_method'], new_params['pattern'])
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        spec = self.translate_to_crd(new_params)
        if 'metric_id' not in new_params.keys():
            spec['metricMethodRef'] = 'hits'
        return spec

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        MappingRules.insert_into_position(maps, new_params, spec)

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'mapping_rules': maps})

    def after_update_list(self, maps, par, new_params):
        """ Returns updated list. """
        return MappingRules.get_from_position(maps, new_params)

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        maps = []
        for mapi in mapsi:
            map_ret = self.translate_to_crd(mapi.entity)
            if not (map_ret['httpMethod'] == spec['httpMethod'] and map_ret['pattern'] == spec['pattern']):
                maps.append(map_ret)
        return maps

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent

    def trans_item(self, key, value, obj):
        """ Translate entity to CRD. """
        if key == 'metric_id':
            if isinstance(obj[key], tuple):
                return obj[key][0]
            met = self.parent.metrics.read(int(obj[key]))
            return met['system_name'].split('.')[0]
        else:
            return obj[key]

    @staticmethod
    def insert_into_position(maps, params, spec):
        """ Inserts entity into right position in list. """
        if 'spec' in spec:
            spec = spec['spec']
        if 'position' in params.keys():
            maps.insert(int(params.pop('position', 1)) - 1, spec)
        elif 'last' in params.keys():
            spec['last'] = True
            maps.append(spec)
        else:
            maps.append(spec)

    @staticmethod
    def get_from_position(maps, params):
        """ Get entity from position in list of entitites."""
        if 'position' in params.keys():
            return maps[int(params['position']) - 1]
        if 'last' in params.keys():
            return maps[-1]
        for mapi in maps:
            if all([params[key] == mapi[key] for key in params.keys()]):
                return mapi
        return None


class BackendMappingRules(MappingRules, threescale_api.resources.BackendMappingRules):
    """
    CRD client for Backend MappingRules.
    """
    SELECTOR = 'Backend'

    def __init__(self, parent, *args, entity_name='mapping_rule',
                 entity_collection='mapping_rules', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""


class ActiveDocs(DefaultClientCRD, threescale_api.resources.ActiveDocs):
    """
    CRD client for ActiveDocs.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_ACTIVE_DOC
    KEYS = constants.KEYS_ACTIVE_DOC
    SELECTOR = 'ActiveDoc'
    ID_NAME = 'activeDocId'

    def __init__(self, parent, *args, entity_name='api_doc',
                 entity_collection='api_docs', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'service_id' in params.keys():
            ide = int(params.pop('service_id'))
            sys_name = Service.id_to_system_name.get(ide, None)
            if not sys_name:
                sys_name = self.parent.services.read(ide)['system_name']
            spec['spec']['productSystemName'] = sys_name
        if 'body' in params.keys():
            params['secret-name'] = params['name'] + 'secret'
            OpenApiRef.create_secret_if_needed(params, self.threescale_client.ocp_namespace)
            spec['spec']['activeDocOpenAPIRef'] = {}
            spec['spec']['activeDocOpenAPIRef']['secretRef'] = {}
            spec['spec']['activeDocOpenAPIRef']['secretRef']['name'] = params['secret-name']

    def before_update(self, new_params, resource):
        """Called before update."""
        if 'service_id' in new_params.keys():
            ide = int(new_params.pop('service_id'))
            sys_name = Service.id_to_system_name.get(ide, None)
            if not sys_name:
                sys_name = self.parent.services.read(ide)['system_name']
            new_params[self.KEYS['service_id']] = sys_name
        if 'body' in new_params.keys():
            if 'secret-name' not in new_params:
                new_params['secret-name'] = new_params['name'] + 'secret'
            OpenApiRef.create_secret_if_needed(new_params, self.threescale_client.ocp_namespace)
            new_params['activeDocOpenAPIRef'] = {}
            new_params['activeDocOpenAPIRef']['secretRef'] = {}
            new_params['activeDocOpenAPIRef']['secretRef']['name'] = new_params['secret-name']


class PoliciesRegistry(DefaultClientCRD, threescale_api.resources.PoliciesRegistry):
    """
    CRD client for PoliciesRegistry.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_POLICY_REG
    KEYS = constants.KEYS_POLICY_REG
    SELECTOR = 'CustomPolicyDefinition'
    ID_NAME = 'policyID'

    def __init__(self, parent, *args, entity_name='policy',
                 entity_collection='policies', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'description' in params['schema'] and isinstance(params['schema']['description'], str):
            params['schema']['description'] = params['schema']['description'].strip()
            if os.linesep in params['schema']['description']:
                params['schema']['description'] = params['schema']['description'].split(os.linesep)
            else:
                params['schema']['description'] = [params['schema']['description']]

    def before_update(self, new_params, resource):
        """Called before update."""
        if 'description' in new_params['schema'] and isinstance(new_params['schema']['description'], str):
            new_params['schema']['description'] = new_params['schema']['description'].strip()
            if os.linesep in new_params['schema']['description']:
                new_params['schema']['description'] = new_params['schema']['description'].split(os.linesep)
            else:
                new_params['schema']['description'] = [new_params['schema']['description']]


class Metrics(DefaultClientNestedCRD, threescale_api.resources.Metrics):
    """
    CRD client for Metrics.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_METRIC
    KEYS = constants.KEYS_METRIC
    SELECTOR = 'Product'
    ID_NAME = 'name'

    def __init__(self, parent, *args, entity_name='metric', entity_collection='metrics',
                 **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params['id'] = (new_params['name'], new_params['unit'])
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        return self.translate_to_crd(new_params)

    def get_list(self, typ=None):
        """ Returns list of entities. """
        return self.parent.metrics.list()

    def in_create(self, maps, params, spec):
        """Do steps to create new instance"""
        name = params.get('name', params.get('system_name', 'hits'))
        if 'name' in spec['spec']:
            spec['spec'].pop('name')
        maps[name] = spec['spec']
        self.parent.update({'metrics': maps})
        for mapi in self.get_list():
            if all([params[key] == mapi[key] for key in params.keys()]):
                return mapi
        return None

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec'].get('metrics', {})

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        name = new_params.get(Metrics.ID_NAME)
        maps[name] = spec

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'metrics': maps})

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        maps = {}
        for mapi in mapsi:
            map_ret = self.translate_to_crd(mapi.entity)
            if map_ret != spec:
                name = mapi[self.ID_NAME]
                maps[name] = map_ret
        return maps

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent

    def trans_item(self, key, value, obj):
        """ Translate entity to CRD. """
        if key != 'name':
            return obj[key]
        return None


class BackendMetrics(Metrics, threescale_api.resources.BackendMetrics):
    """
    CRD client for Backend Metrics.
    """
    SELECTOR = 'Backend'

    def __init__(self, parent, *args, entity_name='metric',
                 entity_collection='metrics', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)


class BackendUsages(DefaultClientNestedCRD, threescale_api.resources.BackendUsages):
    """
    CRD client for BackendUsages.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_BACKEND_USAGE
    KEYS = constants.KEYS_BACKEND_USAGE
    SELECTOR = 'Product'
    ID_NAME = 'name'

    def __init__(self, parent, *args, entity_name='backend_usage',
                 entity_collection='backend_usages', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if "backend_api_id" in params:
            params.update({"backend_id": params.pop("backend_api_id")})

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params['id'] =\
            (new_params['path'], new_params['backend_id'], new_params['service_id'])
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        return self.translate_to_crd(new_params)

    def get_list(self, typ=None):
        """ Returns list of entities. """
        return self.parent.backend_usages.list()

    def in_create(self, maps, params, spec):
        """Do steps to create new instance"""
        backend_id = spec['spec'].pop('backend_id')
        back = self.parent.parent.backends.read(int(backend_id))

        maps[back[self.ID_NAME]] = spec['spec']
        self.parent.update({'backend_usages': maps})
        for mapi in self.get_list():
            if all([params[key] == mapi[key] for key in params.keys()]):
                return mapi
        return None

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec'].get('backend_usages', {})

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        backend_id = spec.pop('backend_id')
        spec.pop('service_id')
        back = self.threescale_client.backends.read(int(backend_id))
        maps[back[BackendUsages.ID_NAME]] = spec

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'backend_usages': maps})

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        maps = {}
        for mapi in mapsi:
            map_ret = self.translate_to_crd(mapi.entity)
            if map_ret != spec:
                backend_id = mapi['backend_id']
                back = self.parent.parent.backends.read(int(backend_id))
                maps[back[self.ID_NAME]] = map_ret
        return maps

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent

    # def trans_item(self, key, value, obj):
    #    """ Translate entity to CRD. """
    #    if key != 'backend_id':
    #        return obj[key]


class Policies(DefaultClientNestedCRD, threescale_api.resources.Policies):
    """
    CRD client for Policies.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_POLICY
    KEYS = constants.KEYS_POLICY
    SELECTOR = 'Product'
    ID_NAME = 'name'

    def __init__(self, parent, *args, entity_name='policy',
                 entity_collection='policies', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params = new_params['policies_config']
        # this should be done because list of policies is already
        # constructed list and not just one item
        spec = []
        for item in new_params:
            if hasattr(item, 'entity'):
                item = item.entity
            spec.append(self.translate_to_crd(item))
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        return spec

    def get_list(self, typ=None):
        """ Returns list of entities. """
        return self.parent.proxy.list().policies.list()

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec'].get('policies', {})

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        maps = spec

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'policies': maps})

    def after_update_list(self, maps, par, new_params):
        """ Returns updated list. """
        return maps

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        return []

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent

    def append(self, *policies):
        pol_list = self.list()
        pol_list['policies_config'].extend(policies)
        return self.update(params=pol_list)

    def insert(self, index: int, *policies):
        pol_list = self.list()['policies_config']
        for (i, policy) in enumerate(policies):
            pol_list.insert(index + i, policy)
        return self.update(params={'policies_config': pol_list})

    def _create_instance_trans(self, instance):
        return {'policies_config': instance}


class ApplicationPlans(DefaultClientNestedCRD, threescale_api.resources.ApplicationPlans):
    """
    CRD client for ApplicationPlans.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_APP_PLANS
    KEYS = constants.KEYS_APP_PLANS
    SELECTOR = 'Product'
    ID_NAME = 'system_name'

    def __init__(self, parent, *args, entity_name='application_plan', entity_collection='plans',
                 **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        spec['spec']['published'] = (params.pop('state_event', 'publish') == 'publish')
        params.update({'setup_fee': '{:.2f}'.format(float(params.get('setup_fee', '0')))})

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params.update({'state_event': new_params.get('state_event', 'publish') == 'publish'})
        new_params.update({'setup_fee': '{:.2f}'.format(float(new_params.get('setup_fee', '0')))})
        new_params['id'] = new_params['system_name']
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        return self.translate_to_crd(new_params)

    def get_list(self, typ=None):
        """ Returns list of entities. """
        return self.parent.app_plans.list()

    def in_create(self, maps, params, spec):
        """Do steps to create new instance"""
        if self.ID_NAME in spec['spec']:
            params[self.ID_NAME] = DefaultClientCRD.normalize(spec['spec'].pop(self.ID_NAME))
        else:
            params[self.ID_NAME] = DefaultClientCRD.normalize(spec['spec'].pop('name'))
        maps[params[self.ID_NAME]] = spec['spec']
        self.parent.update({'application_plans': maps})
        for mapi in self.get_list():
            if all([params[key] == mapi[key] for key in params.keys()]):
                return mapi
        return None

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec'].get('application_plans', {})

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        maps[new_params['id']] = spec

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'application_plans': maps})

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        maps = {}
        for mapi in mapsi:
            map_ret = self.translate_to_crd(mapi.entity)
            if map_ret != spec:
                name = mapi[self.ID_NAME]
                maps[name] = map_ret
        return maps

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent

    def trans_item(self, key, value, obj):
        """ Translate entity to CRD. """
        if key != 'system_name':
            return obj[key]
        return None

    @property
    def plans_url(self) -> str:
        return self.threescale_client.admin_api_url + '/application_plans'


class Accounts(DefaultClientCRD, threescale_api.resources.Accounts):
    """
    CRD client for Accounts.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_ACCOUNT
    KEYS = constants.KEYS_ACCOUNT
    SELECTOR = 'DeveloperAccount'
    ID_NAME = 'accountID'

    def __init__(self, parent, *args, entity_name='account',
                 entity_collection='accounts', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'username' in params:
            pars = params.copy()
            pars['account_name'] = pars['name']
            pars['name'] = secrets.token_urlsafe(8)
            # first user should be admin
            pars['role'] = 'admin'
            self.parent.threescale_client.account_users.create(params=pars)

    def before_update(self, new_params, resource):
        """Called before update."""


class AccountUsers(DefaultClientCRD, threescale_api.resources.AccountUsers):
    """
    CRD client for AccountUsers.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_ACCOUNT_USER
    KEYS = constants.KEYS_ACCOUNT_USER
    SELECTOR = 'DeveloperUser'
    ID_NAME = 'developerUserID'

    def __init__(self, parent, *args, entity_name='user',
                 entity_collection='users', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        password = params.get('password', secrets.token_urlsafe(8))
        password_name = AccountUser.create_password_secret(password, self.threescale_client.ocp_namespace)
        spec['spec']['passwordCredentialsRef']['name'] = password_name
        spec['spec']['developerAccountRef']['name'] = params['account_name']

    def before_update(self, new_params, resource):
        """Called before update."""

    def _is_ready(self, status, new_id):
        """ Is object ready? """
        state = {'Failed': True, 'Invalid': True, 'Orphan': False, 'Ready': False}
        for sta in status['conditions']:
            state[sta['type']] = (sta['status'] == 'True')

        return not state['Failed'] and\
            not state['Invalid'] and\
            state['Orphan'] != state['Ready']


class OpenApis(DefaultClientCRD, threescale_api.defaults.DefaultClient):
    """
    CRD client for OpenApis. This class is only implemented in CRD and not in 3scale API.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_OPEN_API
    KEYS = constants.KEYS_OPEN_API
    SELECTOR = 'OpenAPI'
    ID_NAME = 'productResourceName'

    def __init__(self, parent, *args, entity_name='openapi',
                 entity_collection='openapis', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        if 'url' in params.keys():
            spec['spec']['openapiRef'] = {}
            spec['spec']['openapiRef']['url'] = params.pop('url')
        elif 'body' in params.keys():
            if 'name' not in params:
                joined_name = ''.join(random.choice(string.ascii_letters) for _ in range(16))
                params['name'] = DefaultClientCRD.normalize(joined_name)
            params['secret-name'] = params['name'] + 'secret'
            OpenApiRef.create_secret_if_needed(params, self.threescale_client.ocp_namespace)
            spec['spec']['openapiRef'] = {}
            spec['spec']['openapiRef']['secretRef'] = {}
            spec['spec']['openapiRef']['secretRef']['name'] = params['secret-name']

    def before_update(self, new_params, resource):
        """Called before update."""
        if 'url' in new_params.keys() and 'body' not in new_params.keys():
            new_params['openapiRef'] = {}
            new_params['openapiRef']['url'] = new_params.pop('url')
        elif 'body' in new_params.keys():
            if 'name' not in new_params:
                new_params['name'] = DefaultClientCRD.normalize(
                    ''.join(random.choice(string.ascii_letters) for _ in range(16)))
            new_params['secret-name'] = new_params['name'] + 'secret'
            OpenApiRef.create_secret_if_needed(new_params, self.threescale_client.ocp_namespace)
            new_params['openapiRef'] = {}
            new_params['openapiRef']['secretRef'] = {}
            new_params['openapiRef']['secretRef']['name'] = new_params['secret-name']


class Promotes(DefaultClientCRD, threescale_api.defaults.DefaultClient):
    """
    CRD client for Promotes. This class is only implemented in CRD and not in 3scale API.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_PROMOTE
    KEYS = constants.KEYS_PROMOTE
    SELECTOR = 'ProxyConfigPromote'
    ID_NAME = 'productId'

    def __init__(self, parent, *args, entity_name='promote',
                 entity_collection='promotes', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def before_create(self, params, spec):
        """Called before create."""
        pass

    def before_update(self, new_params, resource):
        """Called before update."""
        pass

    def _is_ready(self, status, new_id):
        """ Is object ready? """
        return status['conditions'][0]['status'] == 'True'


class Tenants(DefaultClientCRD, threescale_api.resources.Tenants):
    """
    CRD client for Tenants.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_TENANT
    KEYS = constants.KEYS_TENANT
    SELECTOR = 'Tenant'
    ID_NAME = 'tenantId'

    def __init__(self, parent, *args, entity_name='tenant',
                 entity_collection='tenants', **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    def _set_provider_ref_new_crd(self, spec):
        """ set provider reference to new crd """
        return spec

    def before_create(self, params, spec):
        """Called before create."""
        spec['spec']['systemMasterUrl'] = self.threescale_client.url
        # create master credentials secret
        mast_sec_name = params['name'] + 'mastsec'
        mas_params = {'MASTER_ACCESS_TOKEN': self.threescale_client.token}
        Tenants.create_secret(mast_sec_name, self.threescale_client.ocp_namespace, mas_params)
        spec['spec']['masterCredentialsRef']['name'] = mast_sec_name
        # create tenant admin secret
        admin_sec_name = params['name'] + 'adminsec'
        admin_params = {'admin_password': params['admin_password']}
        Tenants.create_secret(admin_sec_name, self.threescale_client.ocp_namespace, admin_params)
        spec['spec']['passwordCredentialsRef']['name'] = admin_sec_name

        # tenant sec. ref.
        spec['spec']['tenantSecretRef'] = {
            'name': params['name'] + 'tenant',
            'namespace': self.threescale_client.ocp_namespace
        }

    def before_update(self, new_params, resource):
        """Called before update. Only basic attrs. can be updated,
        sec. references update is not implemented because it is not
        part of origin client."""
        # there are two folds 'signup' and 'account' and new_params should be updated properly
        tmp = new_params.pop('signup')
        new_pars = tmp.pop('account')
        new_pars.update(new_params)
        new_params.clear()
        new_params.update(new_pars)

    @staticmethod
    def create_secret(name, namespace, params):
        """Creates secret if it is needed"""
        spec_sec = copy.deepcopy(constants.SPEC_SECRET)
        spec_sec['metadata']['name'] = name
        spec_sec['metadata']['namespace'] = namespace
        for key, value in params.items():
            spec_sec['data'][key] = base64.b64encode(str(value).encode('ascii')).decode('ascii')
        result = ocp.create(spec_sec)
        assert result.status() == 0

    def read(self, entity_id, **kwargs):
        return DefaultClientCRD.fetch(self, entity_id, **kwargs)

    def _is_ready(self, status, new_id):
        """ Is object ready? """
        # exception because of https://issues.redhat.com/browse/THREESCALE-8273
        return status.get('adminId', None) and status.get('tenantId', None)


class Limits(DefaultClientNestedCRD, threescale_api.resources.Limits):
    """ CRD client for Limits. """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_LIMIT
    KEYS = constants.KEYS_LIMIT
    SELECTOR = 'Product'
    ID_NAME = None
    LIST_TYPE = 'normal'

    def __init__(self, parent, *args, entity_name='limit', entity_collection='limits',
                 metric, **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name,
                         entity_collection=entity_collection, **kwargs)
        self._metric = metric

    def before_create(self, params, spec):
        """Called before create."""
        spec['spec']['metricMethodRef'] = {'systemName': self.metric['name']}
        params['metric_name'] = self.metric['name']
        params['plan_id'] = self.application_plan['id']
        if self.metric.__class__.__name__ == 'BackendMetric':
            spec['spec']['metricMethodRef']['backend'] = self.metric.parent['system_name']
            params['backend_name'] = self.metric.parent['system_name']

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params['id'] = resource.get('id')
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        return self.translate_to_crd(new_params)

    def get_list(self, typ='normal'):
        """ Returns list of entities. """
        Limits.LIST_TYPE = typ
        llist = self.list()
        Limits.LIST_TYPE = 'normal'
        return llist

    def in_create(self, maps, params, spec):
        """Do steps to create new instance"""
        maps = Limits.insert_to_list(maps, params, spec)
        self.parent.update({'limits': maps})
        maps = self.get_list(typ='normal')
        return Limits.get_from_list(maps, params, spec)

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec']['applicationPlans'][self.parent['name']].get('limits', [])

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        spec = self.translate_to_crd(new_params)
        maps = self.insert_to_list(maps, new_params, {'spec': spec})

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'limits': maps})

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        maps = []
        for mapi in mapsi:
            map_ret = self.translate_to_crd(mapi.entity)
            if map_ret != spec:
                maps.append(map_ret)
        return maps

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent.parent

    @staticmethod
    def insert_to_list(maps, params, spec):
        """
        It inserts limit into the list of limits. There can be none or one combination
        of app_plan x metric x period.
        """
        ret = []
        for obj in maps:
            metric_name = ''
            if 'metric_name' in params:
                metric_name = params['metric_name']
            elif 'backend' in obj['metricMethodRef']:
                metric_name = BackendMetric.id_to_system_name[params['metric_id']]
            else:
                metric_name = Metric.id_to_system_name[params['metric_id']]
            if obj['period'] != params['period'] or \
                obj['metricMethodRef']['systemName'] != metric_name:
                ret.append(obj)

        ret.append(spec['spec'])
        return ret

    @staticmethod
    def get_from_list(maps, params, spec):
        """
        It gets limit from the list of limits. There can be none or one combination
        of app_plan x metric x period.
        """
        ret = []
        for obj in maps:
            metric_name = ''
            if 'metric_name' in params:
                metric_name = params['metric_name']
            elif 'backend' in obj['metricMethodRef']:
                metric_name = BackendMetric.id_to_system_name[params['metric_id']]
            else:
                metric_name = Metric.id_to_system_name[params['metric_id']]
            if obj['period'] == params['period'] and \
                obj['metricMethodRef']['systemName'] == metric_name:
                ret.append(obj)

        return ret[0]

    def get_path(self):
        """
        This function is usefull only for Limits and PricingRules and
        it should be redefined there.
        """
        return "spec/applicationPlans/" + self.parent["name"] + "/limits"

    @property
    def metric(self):
        return self._metric

    @property
    def application_plan(self) -> 'ApplicationPlan':
        return self.parent

    def __call__(self, metric: 'Metric' = None) -> 'Limits':
        self._metric = metric
        return self

#    def list_per_app_plan(self, **kwargs):
#        log.info("[LIST] List limits per app plan: %s", kwargs)
#        url = self.parent.url + '/limits'
#        response = self.rest.get(url=url, **kwargs)
#        instance = self._create_instance(response=response)
#        return instance

    def _create_instance_trans(self, instance):
        # it is needed to distinguish between getting metric's limits(normal) or all limits(full)
        if Limits.LIST_TYPE == 'normal':
            if self.metric.__class__.__name__ == 'BackendMetric':
                return [obj for obj in instance \
                        if self.metric['name'] == obj['metric_name'] and \
                        self.metric.parent['system_name'] == obj['backend_name']]
            else:
                return [obj for obj in instance \
                        if self.metric['name'] == obj['metric_name'] and \
                        'backend_name' not in obj.entity]
        else:
            return [obj for obj in instance]


class PricingRules(DefaultClientNestedCRD, threescale_api.resources.PricingRules):
    """ CRD client for PricingRules. """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_PRICING_RULE
    KEYS = constants.KEYS_PRICING_RULE
    SELECTOR = 'Product'
    ID_NAME = None
    LIST_TYPE = 'normal'

    def __init__(self, parent, *args, entity_name='pricing_rule', entity_collection='pricing_rules',
                 metric, **kwargs):
        super().__init__(*args, parent=parent, entity_name=entity_name,
                         entity_collection=entity_collection, **kwargs)
        self._metric = metric

    def before_create(self, params, spec):
        """Called before create."""
        spec['spec']['metricMethodRef'] = {'systemName': self.metric['name']}
        params['metric_name'] = self.metric['name']
        params['plan_id'] = self.application_plan['id']
        if self.metric.__class__.__name__ == 'BackendMetric':
            spec['spec']['metricMethodRef']['backend'] = self.metric.parent['system_name']
            params['backend_name'] = self.metric.parent['system_name']

        if 'cost_per_unit' in params:
            params['cost_per_unit'] = str(params['cost_per_unit'])

    def before_update(self, new_params, resource):
        """Called before update."""
        new_params['id'] = resource.get('id')
        if resource and 'id' in new_params:
            resource.entity_id = new_params['id']
        if 'cost_per_unit' in new_params:
            new_params['cost_per_unit'] = str(new_params['cost_per_unit'])
        return self.translate_to_crd(new_params)

    def get_list(self, typ='normal'):
        """ Returns list of entities. """
        PricingRules.LIST_TYPE = typ
        llist = self.list()
        PricingRules.LIST_TYPE = 'normal'
        return llist

    def in_create(self, maps, params, spec):
        """Do steps to create new instance"""
        maps = PricingRules.insert_to_list(maps, params, spec)
        self.parent.update({'pricingRules': maps})
        maps = self.get_list(typ='normal')
        return PricingRules.get_from_list(maps, params, spec)

    def get_list_from_spec(self):
        """ Returns list from spec """
        return self.parent.crd.as_dict()['spec']['applicationPlans'][self.parent['name']].get('pricingRules', [])

    def before_update_list(self, maps, new_params, spec, resource):
        """ Modify some details in data before updating the list """
        spec = self.translate_to_crd(new_params)
        maps = PricingRules.insert_to_list(maps, new_params, {'spec': spec})

    def update_list(self, maps):
        """ Returns updated list. """
        return self.parent.update({'pricingRules': maps})

    def remove_from_list(self, mapsi, spec):
        """ Returns list without item specified by 'spec'. """
        maps = []
        for mapi in mapsi:
            map_ret = self.translate_to_crd(mapi.entity)
            if map_ret != spec:
                maps.append(map_ret)
        return maps

    def topmost_parent(self):
        """
        Returns topmost parent. In most cases it is the same as parent
        except of Limits and PricingRules
        """
        return self.parent.parent

    @staticmethod
    def insert_to_list(maps, params, spec):
        """
        It inserts limit into the list of limits. There can be none or one combination
        of app_plan x metric x period.
        """
        ret = []
        for obj in maps:
            metric_name = ''
            if 'metric_name' in params:
                metric_name = params['metric_name']
            elif 'backend' in obj['metricMethodRef']:
                metric_name = BackendMetric.id_to_system_name[params['metric_id']]
            else:
                metric_name = Metric.id_to_system_name[params['metric_id']]
            if obj['from'] != params['min'] or obj['to'] != params['max'] or \
                obj['metricMethodRef']['systemName'] != metric_name:
                ret.append(obj)

        ret.append(spec['spec'])
        return ret

    @staticmethod
    def get_from_list(maps, params, spec):
        """
        It gets limit from the list of limits. There can be none or one combination
        of app_plan x metric x period.
        """
        ret = []
        for obj in maps:
            metric_name = ''
            if 'metric_name' in params:
                metric_name = params['metric_name']
            elif 'backend' in obj['metricMethodRef']:
                metric_name = BackendMetric.id_to_system_name[params['metric_id']]
            else:
                metric_name = Metric.id_to_system_name[params['metric_id']]
            if obj['min'] == params['min'] and obj['max'] == params['max'] and \
                obj['metricMethodRef']['systemName'] == metric_name:
                ret.append(obj)

        return ret[0]

    def get_path(self):
        """
        This function is usefull only for Limits and PricingRules and
        it should be redefined there.
        """
        return "spec/applicationPlans/" + self.parent["name"] + "/pricingRules"

#    def trans_item(self, key, value, obj):
#        """ Translate entity to CRD. """
#        if key != 'name':
#            return obj[key]

    @property
    def metric(self):
        return self._metric

    @property
    def application_plan(self) -> 'ApplicationPlan':
        return self.parent

    def __call__(self, metric: 'Metric' = None) -> 'PricingRules':
        self._metric = metric
        return self

#    def list_per_app_plan(self, **kwargs):
#        log.info("[LIST] List limits per app plan: %s", kwargs)
#        url = self.parent.url + '/limits'
#        response = self.rest.get(url=url, **kwargs)
#        instance = self._create_instance(response=response)
#        return instance

    def _create_instance_trans(self, instance):
        # it is needed to distinguish between getting metric's limits(normal) or all limits(full)
        if PricingRules.LIST_TYPE == 'normal':
            if self.metric.__class__.__name__ == 'BackendMetric':
                return [obj for obj in instance \
                        if self.metric['name'] == obj['metric_name'] and \
                        self.metric.parent['system_name'] == obj['backend_name']]
            else:
                return [obj for obj in instance \
                        if self.metric['name'] == obj['metric_name'] and \
                        'backend_name' not in obj.entity]
        else:
            return [obj for obj in instance]


class Applications(DefaultClientCRD, threescale_api.resources.Applications):
    """
    CRD client for Applications.
    """
    CRD_IMPLEMENTED = True
    SPEC = constants.SPEC_APPLICATION
    KEYS = constants.KEYS_APPLICATION
    SELECTOR = 'Application'
    ID_NAME = 'applicationID'

    def __init__(self, parent, account, *args, entity_name='application',
                 entity_collection='applications', **kwargs):
        self.account = account
        self._url = (account.client.url + '/' + str(account.entity_id)) if account else parent.url
        self._url += '/applications'
        super().__init__(*args, parent=parent, entity_name=entity_name, entity_collection=entity_collection, **kwargs)

    @property
    def url(self) -> str:
        return self._url

    def before_create(self, params, spec):
        """Called before create."""
        service = self.parent.services.read(params.pop('service_id'))
        plan = service.app_plans.read(params['plan_id'])
        spec['spec']['productCR']['name'] = service['system_name']
        spec['spec']['accountCR']['name'] = self.account['name']
        spec['spec']['applicationPlanName'] = plan['system_name']

    def before_update(self, new_params, resource):
        """Called before update."""
        pass

    def _is_ready(self, status, new_id):
        """ Is object ready? """
        return status['conditions'][0]['status'] == 'True'

    def trans_item(self, key, value, obj):
        """ Translate entity to CRD. """
        if key in ['service_name', 'account_name']:
            return {'name': obj[key]}
        else:
            return obj[key]

# Resources
# DefaultResourceCRD,


class Service(DefaultResourceCRD, threescale_api.resources.Service):
    """
    CRD resource for Service.
    """
    GET_PATH = 'spec'
    system_name_to_id = {}
    id_to_system_name = {}

    def __init__(self, entity_name='system_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            entity = {}
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            for key, value in spec.items():
                for cey, walue in constants.KEYS_SERVICE.items():
                    if key == walue:
                        entity[cey] = value
            entity['id'] = crd.as_dict().get('status').get(Services.ID_NAME)
            # add ids to cache
            if entity['id'] and entity['system_name']:
                Service.id_to_system_name[int(entity['id'])] = entity['system_name']
                Service.system_name_to_id[entity['system_name']] = int(entity['id'])
            auth = crd.model.spec.get('deployment', None)
            # TODO add better authentication work
            if auth:
                auth = auth.popitem()[1]
            if auth and 'authentication' in auth:
                auth = list(auth['authentication'].keys())[0]
                entity['backend_version'] = constants.SERVICE_AUTH[auth]
            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def mapping_rules(self) -> 'MappingRules':
        return MappingRules(instance_klass=MappingRule, parent=self)

    @property
    def proxy(self) -> 'Proxies':
        return Proxies(parent=self, instance_klass=Proxy)

    @property
    def policies_registry(self) -> 'PoliciesRegistry':
        return PoliciesRegistry(parent=self, instance_klass=PoliciesRegistry)

    @property
    def metrics(self) -> 'Metrics':
        return Metrics(instance_klass=Metric, parent=self)

    @property
    def backend_usages(self) -> 'BackendUsages':
        return BackendUsages(instance_klass=BackendUsage, parent=self)

    @property
    def app_plans(self) -> 'ApplicationPlans':
        return ApplicationPlans(instance_klass=ApplicationPlan, parent=self)


class Proxy(DefaultResourceCRD, threescale_api.resources.Proxy):
    """
    CRD resource for Proxy.
    """

    GET_PATH = 'spec/deployment'

    def __init__(self, **kwargs):
        # store oidc dict
        self.oidc = {'oidc_configuration': {}}
        self.security = False
        self.responses = False
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            # client = kwargs.get('client')
            self.spec_path = []
            entity = {}
            # apicastHosted or ApicastSelfManaged
            if len(spec.values()):
                apicast_key = list(spec.keys())[0]
                if apicast_key == 'apicastHosted':
                    entity['deployment_option'] = 'hosted'
                elif apicast_key == 'apicastSelfManaged':
                    entity['deployment_option'] = 'self_managed'
                self.spec_path.append(apicast_key)
                # add endpoint and sandbox_endpoint
                for key, value in spec.items():
                    for cey, walue in constants.KEYS_PROXY.items():
                        if key == walue:
                            entity[cey] = value

                spec = list(spec.values())[0].get('authentication', {})
                self.spec_path.append('authentication')
                # userkey or appKeyAppID or oidc
                if spec and len(spec.values()):
                    self.spec_path.append(list(spec.keys())[0])
                    spec = list(spec.values())[0]
                    # add credentials_location
                    for key, value in spec.items():
                        if key == 'authenticationFlow':
                            for key2, value2 in spec[key].items():
                                for cey, walue in constants.KEYS_OIDC.items():
                                    if key2 == walue:
                                        self.oidc['oidc_configuration'][cey] = value2
                        else:
                            for cey, walue in constants.KEYS_PROXY.items():
                                if key == walue:
                                    entity[cey] = value

                    secret = spec.get('security', {})
                    if secret:
                        self.secret = True
                    for key, value in secret.items():
                        for cey, walue in constants.KEYS_PROXY_SECURITY.items():
                            if key == walue:
                                entity[cey] = value
                    spec = spec.get('gatewayResponse', {})
                    if spec:
                        self.responses = True
                        for key, value in spec.items():
                            for cey, walue in constants.KEYS_PROXY_RESPONSES.items():
                                if key == walue:
                                    entity[cey] = value

            super().__init__(crd=crd, entity=entity, **kwargs)

            # there is 'endpoint' and 'sandbox_endpoint' just in apicastSelfManaged and not in apicastHosted
            if ('endpoint' not in entity) or ('sandbox_endpoint' not in entity):
                self.client.disable_crd_implemented()
                self.parent.client.disable_crd_implemented()
                tmp_proxy = threescale_api.resources.Services.read(self.parent.client,
                                                                   self.parent.entity_id).proxy.fetch()
                for name in ['endpoint', 'sandbox_endpoint']:
                    self.entity[name] = tmp_proxy[name]
                self.client.enable_crd_implemented()
                self.parent.client.enable_crd_implemented()
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(**kwargs)

    def deploy(self):
        """
        Deploy to staging.
        """
        params = {'productCRName': self.parent.crd.as_dict()['metadata']['name']}
        prom = self.threescale_client.promotes.create(params)
        ide = prom.entity.get('id', None)
        prom.delete()
        if ide and int(ide) == self.parent['id']:
            return True
        else:
            return False

    def promote(self, **kwargs):
        """
        Promotes staging proxy to production. CRD implementation promotes to staging
        if there is any proxy config ready to be promoted to staging and then it is
        promoted to production. If user would like to have different proxy configurations
        if production and in staging then it should be promoted to production first and
        to staging. It is not possible to promote specific proxy configuration
        to production nor to staging.
        """
        params = {'productCRName': self.parent.crd.as_dict()['metadata']['name'],
                  'production': True}
        prom = self.threescale_client.promotes.create(params)
        ide = prom.entity.get('id', None)
        prom.delete()
        if ide and int(ide) == self.parent['id']:
            return True
        else:
            return False

    @property
    def service(self) -> 'Service':
        return self.parent

    @property
    def mapping_rules(self) -> MappingRules:
        return self.parent.mapping_rules

    @property
    def policies(self) -> 'Policies':
        return Policies(parent=self.parent, instance_klass=Policy)

    # def get_item_attribute(self, item: str):
    #    if not isinstance(item, str):
    #        return self.entity.get(item)
    #    if item in self.entity:
    #        return self.entity.get(item)
    #    else:
    #        self.client.__class__.CRD_IMPLEMENTED = False
    #        LOG.info(f"[GET ATTRIBUTE] CRD {self.client._entity_name} {item}")
    #        pr_ent = self.service.proxy.list().get(item)
    #        self.client.__class__.CRD_IMPLEMENTED = True
    #        return pr_ent.get(item)

    # def __getitem__(self, item: str):
    #    return self.get_item_attribute(item)
    #
    # def get(self, item):
    #     return self.get_item_attribute(item)


class OIDCConfigs(threescale_api.resources.DefaultClient):
    """ OIDC configs. """

    def update(self, params: dict = None, **kwargs):
        proxy = self.parent.list()
        proxy.oidc['oidc_configuration'].update(params['oidc_configuration'])
        proxy.update()

    def read(self, params: dict = None, **kwargs):
        proxy = self.parent.list()
        return proxy.oidc


class MappingRule(DefaultResourceCRD, threescale_api.resources.MappingRule):
    """
    CRD resource for MappingRule.
    """
    GET_PATH = 'spec/mappingRules'

    def __init__(self, entity_name='system_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_MAPPING_RULE.items():
                    if key == walue:
                        entity[cey] = value
            # simulate entity_id by list of attributes
            entity['id'] = (entity['http_method'], entity['pattern'])
            self.entity_id = entity.get('id')

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
            # TODO
            if 'metric_id' in entity and isinstance(entity['metric_id'], str):
                met_system_name = None
                # if self.parent.__class__.__name__ == 'Backend' and ('.' not in entity['metric_id']):
                #     met_system_name = entity['metric_id'] + '.' + str(self.parent['id'])
                # else:
                met_system_name = entity['metric_id']
                met = self.parent.metrics.read_by(**{'name': met_system_name})
                entity['metric_id'] = met['id']
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    # TODO
    @property
    def proxy(self) -> 'Proxy':
        ser = self

        class FakeProxy():
            """ This is simulation of Proxy class because
            of right encapsulation for mapping rules."""
            def mapping_rules(self):
                """ Returns mapping rules client related to the Proxy. """
                return ser.mapping_rules

        return FakeProxy()

    @property
    def service(self) -> 'Service':
        return self.parent

#    @property
#    def entity_id(self) -> int:
#        return self._entity_id or self._entity.get('id')
#
#    @entity_id.setter
#    def entity_id(self, value=None):
#        self._entity_id = value or self._entity.get('id')


class OpenApiRef():
    """ Open API reference."""
    @staticmethod
    def load_openapi(entity, spec):
        """
        if OAS is referenced by url:
        1) OAS is loaded to body
        2) when body is updated(call update or create method),
            secret is created and it replaces reference by url

        if OAS is referenced by secret:
        1) OAS is loaded from secret and stored into body
        2) when body is updated, secret is changed
        """

        if 'url' in spec:
            url = spec['url']
            entity['url'] = url
            res = requests.get(url)
            if url.endswith('.yaml') or url.endswith('.yml'):
                entity['body'] = json.dumps(yaml.load(res.content, Loader=yaml.SafeLoader))
            else:
                entity['body'] = res.content
        elif 'secretRef' in spec:
            secret_name = spec['secretRef']['name']
            secret = ocp.selector('secret/' + secret_name).objects()[0]
            enc_body = list(secret.as_dict()['data'].values())[0]
            entity['body'] = base64.b64decode(enc_body).decode('ascii')

    @staticmethod
    def create_secret_if_needed(params, namespace):
        """Creates secret for tenant."""
        body_ascii = str(params['body']).encode('ascii')
        body_enc = base64.b64encode(body_ascii)
        spec_sec = copy.deepcopy(constants.SPEC_SECRET)
        spec_sec['metadata']['name'] = params['secret-name']
        spec_sec['metadata']['namespace'] = namespace
        spec_sec['data'][params['secret-name']] = body_enc.decode('ascii')
        result = ocp.selector('secret/' + params['secret-name'])
        if result.status() == 0:
            objs = result.objects()
            if objs:
                objs[0].delete()
        result = ocp.create(spec_sec)
        assert result.status() == 0
        if 'url' in params:
            del params['url']
        del params['body']


class ActiveDoc(DefaultResourceCRD, threescale_api.resources.ActiveDoc):
    """
    CRD resource for ActiveDoc.
    """
    GET_PATH = 'spec'

    def __init__(self, entity_name='system_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_ACTIVE_DOC.items():
                    if key == walue:
                        entity[cey] = value
            entity['id'] = crd.as_dict().get('status').get(ActiveDocs.ID_NAME)
            if 'service_id' in entity:
                ide = Service.system_name_to_id.get(entity['service_id'], None)
                if not ide:
                    ide = kwargs['client'].parent.services.read_by_name(entity['service_id'])['id']
                entity['service_id'] = ide

            OpenApiRef.load_openapi(entity, spec['activeDocOpenAPIRef'])

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)


class PolicyRegistry(DefaultResourceCRD, threescale_api.resources.PolicyRegistry):
    """
    CRD resource for PolicyRegistry.
    """
    GET_PATH = 'spec'

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
# unit tests pass, this should be verify on real tests
#            if 'description' in spec['schema'] and isinstance(spec['schema']['description'], list):
#                spec['schema']['description'] = os.linesep.join(spec['schema']['description'])
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_POLICY_REG.items():
                    if key == walue:
                        entity[cey] = value
            entity['id'] = crd.as_dict().get('status').get(PoliciesRegistry.ID_NAME)
            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)


class Backend(DefaultResourceCRD, threescale_api.resources.Backend):
    """
    CRD resource for Backend.
    """
    GET_PATH = 'spec'

    def __init__(self, entity_name='system_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_BACKEND.items():
                    if key == walue:
                        entity[cey] = value
            entity['id'] = crd.as_dict().get('status').get(Backends.ID_NAME)

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def mapping_rules(self) -> 'BackendMappingRules':
        return BackendMappingRules(parent=self, instance_klass=BackendMappingRule)

    @property
    def metrics(self) -> 'BackendMetrics':
        return BackendMetrics(parent=self, instance_klass=BackendMetric)

    @property
    def usages(self) -> 'BackendUsages':
        for service in self.client.threescale_client.services.list():
            backend_usages = service.backend_usages.list()
            if len(backend_usages) > 0 and int(backend_usages[0]['backend_id']) == int(self['id']):
                return BackendUsages(parent=service, instance_klass=BackendUsage)
        return None


class BackendMappingRule(MappingRule):
    """
    CRD resource for Backend MappingRule.
    """
    GET_PATH = 'spec/mappingRules'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Metric(DefaultResourceCRD, threescale_api.resources.Metric):
    """
    CRD resource for Metric.
    """
    GET_PATH = 'spec/metrics'
    system_name_to_id = {}
    id_to_system_name = {}

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            # client = kwargs.get('client')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_METRIC.items():
                    if key == walue:
                        entity[cey] = value
            # simulate id because CRD has no ids
            entity['id'] = (entity['name'], entity['unit'])
            self.entity_id = entity.get('id')
            # it is not possible to simulate id here because
            # it is used in BackendMappingRules, which is not implemented
            # entity['id'] = Metric.system_name_to_id.get(entity['name'], None)
            # if not entity['id']:
            #    client.__class__.CRD_IMPLEMENTED = False
            #    entity['id'] = threescale_api.resources.Metrics.read_by_name(
            #        client,
            #        entity['name'] + '.' + str(client.parent.entity_id)).entity_id
            #    Metric.system_name_to_id[entity['name']] = int(entity['id'])
            #    Metric.id_to_system_name[entity['id']] = entity['name']
            #    client.__class__.CRD_IMPLEMENTED = True

            self.entity_id = entity['id']
            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def service(self) -> 'Service':
        return self.parent

#    @property
#    def entity_id(self) -> int:
#        return self._entity_id or self._entity.get('id')
#
#    @entity_id.setter
#    def entity_id(self, value=None):
#        self._entity_id = value or self._entity.get('id')


class BackendMetric(Metric):
    """
    CRD resource for Backend Metric.
    """

    GET_PATH = 'spec/metrics'
    system_name_to_id = {}
    id_to_system_name = {}

    def __init__(self, entity_name='system_name', *args, **kwargs):
        super().__init__(entity_name=entity_name, *args, **kwargs)


class BackendUsage(DefaultResourceCRD, threescale_api.resources.BackendUsage):
    """
    CRD resource for BackendUsage.
    """

    GET_PATH = 'spec/backendUsages'

    def __init__(self, entity_name='system_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            client = kwargs.get('client')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_BACKEND_USAGE.items():
                    if key == walue:
                        entity[cey] = value
            entity['service_id'] = int(crd.as_dict().get('status', {}).get(Services.ID_NAME, 0))
            back = client.threescale_client.backends.read_by_name(spec['name'])
            entity['backend_id'] = int(back['id'])
            # simulate entity_id by list of attributes
            entity['id'] = (entity['path'], entity['backend_id'], entity['service_id'])
            self.entity_id = entity.get('id')

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def service(self) -> 'Service':
        """Returns service related to backend usage"""
        return self.parent

#    @property
#    def entity_id(self) -> int:
#        return self._entity_id or self._entity.get('id')
#
#    @entity_id.setter
#    def entity_id(self, value=None):
#        self._entity_id = value or self._entity.get('id')


class ApplicationPlan(DefaultResourceCRD, threescale_api.resources.ApplicationPlan):
    """
    CRD resource for ApplicationPlan.
    """
    GET_PATH = 'spec/applicationPlans'
    system_name_to_id = {}
    id_to_system_name = {}

    def __init__(self, entity_name='system_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            client = kwargs.get('client')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_APP_PLANS.items():
                    if key == walue:
                        entity[cey] = value
            if 'system_name' in spec:
                entity['name'] = spec['system_name']
            spec['state_event'] = 'publish' if spec.get('state_event', False) else 'unpublish'
            # simulate id because CRD has no ids
            # entity['id'] = entity['name']
            # it is not possible to simulate id here because it is used in Application, which is not implemented
            entity['id'] = ApplicationPlan.system_name_to_id.get(entity['system_name'], None)
            if not entity['id']:
                client.disable_crd_implemented()
                plan = threescale_api.resources.ApplicationPlans.read_by_name(client, entity['system_name'])
                entity['id'] = plan['id']
                ApplicationPlan.system_name_to_id[entity['system_name']] = int(entity['id'])
                ApplicationPlan.id_to_system_name[entity['id']] = entity['system_name']
                client.enable_crd_implemented()
            self.entity_id = entity.get('id')

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def service(self) -> 'Service':
        """Returns service related to app. plan"""
        return self.parent

    def limits(self, metric):
        """Returns limits"""
        return Limits(self, metric=metric, instance_klass=Limit)

    def pricing_rules(self, metric):
        """Returns limits"""
        return PricingRules(self, metric=metric, instance_klass=PricingRule)

    @property
    def plans_url(self) -> str:
        """Returns url to app. plans"""
        return self.threescale_client.admin_api_url + f"/application_plans/{self.entity_id}"


class Account(DefaultResourceCRD, threescale_api.resources.Account):
    """
    CRD resource for Account.
    """
    GET_PATH = 'spec'

    def __init__(self, entity_name='org_name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_ACCOUNT.items():
                    if key == walue:
                        entity[cey] = value
            status = crd.as_dict().get('status', None)
            if status:
                entity['id'] = status.get(Accounts.ID_NAME)
            entity['name'] = crd.as_dict().get('metadata', {}).get('name')

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def users(self) -> AccountUsers:
        account = self

        class FakeAccountUsers(AccountUsers):
            """ Simulating AccountUsers class
            to be able to process Account/AccountUsers workflow in CRDs.
            """
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.parent = account

            # list should be rewritten because AccountUsers is not parent of Accounts
            def list(self, **kwargs):
                LOG.info(self._log_message("[LIST] FakeAccountUsers CRD", args=kwargs))
                if account:
                    return self.select_by(**{'account_name': account['name']})
                return self._list(**kwargs)

            @property
            def url(self) -> str:
                return account.url + '/users'

        return FakeAccountUsers(parent=self.parent, instance_klass=AccountUser)

    @property
    def applications(self) -> Applications:
        return Applications(parent=self.parent, instance_klass=Application, account=self)


class AccountUser(DefaultResourceCRD, threescale_api.resources.AccountUser):
    """
    CRD resource for AccountUser.
    """
    GET_PATH = 'spec'

    def __init__(self, entity_name='username', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_ACCOUNT_USER.items():
                    if key == walue:
                        entity[cey] = value
            status = crd.as_dict().get('status', None)
            if status:
                entity['id'] = status.get(AccountUsers.ID_NAME)
            # link to account because AccountUser is not nested class of Account
            entity['account_name'] = spec['developerAccountRef']['name']

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity=entity, entity_name=entity_name, **kwargs)

    @staticmethod
    def create_password_secret(password, namespace):
        """ Creates password in secret. """
        password_ascii = str(password).encode('ascii')
        password_enc = base64.b64encode(password_ascii)
        spec_sec = copy.deepcopy(constants.SPEC_SECRET)
        name = secrets.token_urlsafe(8).lower().replace('_', '')
        spec_sec['metadata']['name'] = name
        spec_sec['metadata']['namespace'] = namespace
        spec_sec['data']['password'] = password_enc.decode('ascii')
        result = ocp.create(spec_sec)
        assert result.status() == 0
        return name

    # @property
    # def permissions(self) -> 'UserPermissionsClient':
    #     return UserPermissionsClient(parent=self, instance_klass=UserPermissions)


class Policy(DefaultResourceCRD, threescale_api.resources.Policy):
    """
    CRD resource for Policy.
    """
    GET_PATH = 'spec/policies'

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            # client = kwargs.get('client')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_POLICY.items():
                    if key == walue:
                        entity[cey] = value
            entity['service_id'] = int(crd.as_dict().get('status', {}).get(Services.ID_NAME, 0))
            # simulate entity_id by list of attributes
            entity['id'] = (entity['service_id'], entity['name'])
            self.entity_id = entity.get('id')

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity=entity, entity_name=entity_name, **kwargs)

    @property
    def service(self) -> 'Service':
        return self.parent

#    @property
#    def entity_id(self) -> int:
#        return self._entity_id or self._entity.get('id')
#
#    @entity_id.setter
#    def entity_id(self, value=None):
#        self._entity_id = value or self._entity.get('id')


class OpenApi(DefaultResourceCRD):
    """
    CRD resource for OpenApi.
    """

    GET_PATH = 'spec'

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        crd = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')

            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_OPEN_API.items():
                    if key == walue:
                        entity[cey] = value
            entity['id'] = crd.as_dict().get('status').get(OpenApis.ID_NAME)
            OpenApiRef.load_openapi(entity, spec['openapiRef'])

        super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)


class Tenant(DefaultResourceCRD, threescale_api.resources.Tenant):
    """
    CRD resource for Policy.
    """

    FOLD = ["signup", "account"]

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            entity = {Tenant.FOLD[0]: {Tenant.FOLD[1]: {}}}
            insert = entity[Tenant.FOLD[0]][Tenant.FOLD[1]]
            for key, value in spec.items():
                for cey, walue in constants.KEYS_TENANT.items():
                    if key == walue:
                        insert[cey] = value

            insert['id'] = crd.as_dict()['status'][Tenants.ID_NAME]
            self.entity_id = insert.get('id')
            # get secret created by operator
            sec_data = ocp.selector('secret/' + insert['tenantSecretRef']['name']).objects()[0].as_dict()['data']
            insert['admin_base_url'] = base64.b64decode(sec_data['adminURL'])
            entity[Tenant.FOLD[0]]['access_token'] = {'value': base64.b64decode(sec_data['token'])}
            insert['base_url'] = insert['admin_base_url']

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)


#    @property
#    def entity_id(self) -> int:
#        return self.entity[Tenant.FOLD[0]][Tenant.FOLD[1]]["id"]


class Limit(DefaultResourceCRD, threescale_api.resources.Limit):
    """
    CRD resource for Limit.
    """
    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            client = kwargs.get('client')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_LIMIT.items():
                    if key == walue:
                        entity[cey] = value
            entity['plan_id'] = client.parent['id']
            entity['metric_name'] = spec['metricMethodRef']['systemName']
            backend = None
            if 'backend' in spec['metricMethodRef']:
                entity['backend_name'] = spec['metricMethodRef']['backend']
                entity['metric_id'] = BackendMetric.system_name_to_id.get(entity['metric_name'], None)
                backend = client.threescale_client.backends.read_by_name(entity['backend_name'])
                # simulate id because CRD has no ids
                entity['id'] = (entity['period'], entity['metric_name'], entity['backend_name'])
            else:
                entity['metric_id'] = Metric.system_name_to_id.get(entity['metric_name'], None)
                # simulate id because CRD has no ids
                entity['id'] = (entity['period'], entity['metric_name'])
            self.entity_id = entity.get('id')
            if not entity['metric_id']:
                if 'backend' in spec['metricMethodRef']:
                    backend.metrics.disable_crd_implemented()
                    entity['metric_id'] = int(threescale_api.resources.BackendMetrics.read_by_name(
                        backend.metrics,
                        entity['metric_name'] + '.' + str(backend['id'])).entity_id)
                    BackendMetric.system_name_to_id[entity['metric_name']] = entity['metric_id']
                    BackendMetric.id_to_system_name[entity['metric_id']] = entity['metric_name']
                    backend.metrics.enable_crd_implemented()
                else:
                    client.topmost_parent().metrics.disable_crd_implemented()
                    entity['metric_id'] = int(threescale_api.resources.Metrics.read_by_name(
                        client.topmost_parent().metrics,
                        entity['metric_name']).entity_id)
                    Metric.system_name_to_id[entity['metric_name']] = entity['metric_id']
                    Metric.id_to_system_name[entity['metric_id']] = entity['metric_name']
                    client.topmost_parent().metrics.enable_crd_implemented()

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def app_plan(self) -> ApplicationPlan:
        return self.parent


class PricingRule(DefaultResourceCRD, threescale_api.resources.PricingRule):
    """
    CRD resource for PricingRule.
    """
    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            client = kwargs.get('client')
            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_PRICING_RULE.items():
                    if key == walue:
                        entity[cey] = value
            entity['plan_id'] = client.parent['id']
            entity['metric_name'] = spec['metricMethodRef']['systemName']
            backend = None
            if 'backend' in spec['metricMethodRef']:
                entity['backend_name'] = spec['metricMethodRef']['backend']
                entity['metric_id'] = BackendMetric.system_name_to_id.get(entity['metric_name'], None)
                backend = client.threescale_client.backends.read_by_name(entity['backend_name'])
                # simulate id because CRD has no ids
                entity['id'] = (entity['min'], entity['max'], entity['metric_name'], entity['backend_name'])
            else:
                entity['metric_id'] = Metric.system_name_to_id.get(entity['metric_name'], None)
                # simulate id because CRD has no ids
                entity['id'] = (entity['min'], entity['max'], entity['metric_name'])
            self.entity_id = entity.get('id')
            if not entity['metric_id']:
                if 'backend' in spec['metricMethodRef']:
                    backend.metrics.disable_crd_implemented()
                    entity['metric_id'] = int(threescale_api.resources.BackendMetrics.read_by_name(
                        backend.metrics,
                        entity['metric_name'] + '.' + str(backend['id'])).entity_id)
                    BackendMetric.system_name_to_id[entity['metric_name']] = entity['metric_id']
                    BackendMetric.id_to_system_name[entity['metric_id']] = entity['metric_name']
                    backend.metrics.enable_crd_implemented()
                else:
                    client.topmost_parent().metrics.disable_crd_implemented()
                    entity['metric_id'] = int(threescale_api.resources.Metrics.read_by_name(
                        client.topmost_parent().metrics,
                        entity['metric_name']).entity_id)
                    Metric.system_name_to_id[entity['metric_name']] = entity['metric_id']
                    Metric.id_to_system_name[entity['metric_id']] = entity['metric_name']
                    client.topmost_parent().metrics.enable_crd_implemented()

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def app_plan(self) -> ApplicationPlan:
        return self.parent


class Promote(DefaultResourceCRD):
    """
    CRD resource for ProxyConfigPromote.
    """

    GET_PATH = 'spec'

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        crd = None
        if 'spec' in kwargs:
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')

            entity = {}
            for key, value in spec.items():
                for cey, walue in constants.KEYS_PROMOTE.items():
                    if key == walue:
                        entity[cey] = value
            entity['id'] = crd.as_dict().get('status', {}).get(Promotes.ID_NAME, None)

        super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)


class Application(DefaultResourceCRD, threescale_api.resources.Application):
    """
    CRD resource for Application.
    """
    GET_PATH = 'spec'

    def __init__(self, entity_name='name', **kwargs):
        entity = None
        if 'spec' in kwargs:
            entity = {}
            spec = kwargs.pop('spec')
            crd = kwargs.pop('crd')
            for key, value in spec.items():
                for cey, walue in constants.KEYS_APPLICATION.items():
                    if key == walue:
                        entity[cey] = value
            status = crd.as_dict().get('status')
            entity['id'] = status.get(Applications.ID_NAME)
            entity['state'] = status.get('state')

            entity['service_name'] = spec.get('productCR').get('name')
            entity['account_name'] = spec.get('accountCR').get('name')

            # load auth keys
            client = kwargs['client']
            client.disable_crd_implemented()
            acc = client.parent.accounts.select_by(name=entity['account_name'])[0]
            app = acc.applications.read(entity['id'])
            if 'user_key' in app.entity.keys():
                entity['user_key'] = app['user_key']
            elif 'application_id' in app.entity.keys():
                entity['application_id'] = app['application_id']
            client.enable_crd_implemented()

            super().__init__(crd=crd, entity=entity, entity_name=entity_name, **kwargs)
        else:
            # this is not here because of some backup, but because we need to have option
            # to creater empty object without any data. This is related to "lazy load"
            super().__init__(entity_name=entity_name, **kwargs)

    @property
    def service(self) -> 'Service':
        "The service to which this application is bound"
        return self.parent.services.read_by_name(self.entity['service_name'])

    @property
    def account(self) -> 'Account':
        if self.client.account:
            return self.client.account
        else:
            return self.parent.accounts.read_by_name(self.entity['account_name'])

    def set_state(self, state: str):
        """Sets the state for the resource
        Args:
            state(str): Which state
            **kwargs: Optional args

        Returns(Application): Application resource instance
        """
        if state == 'suspend':
            return self.update({'suspend': True})
        if state == 'resume':
            return self.update({'suspend': False})
        return self

