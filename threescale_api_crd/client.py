"""
Module with ThreeScaleClient for CRD.
"""

import openshift_client as ocp
from openshift_client import OpenShiftPythonException
import threescale_api
from threescale_api_crd import resources


class ThreeScaleClientCRD(threescale_api.client.ThreeScaleClient):
    """
    Threescale client for CRD.
    """

    def __init__(
        self, url, token, ocp_provider_ref=None, ocp_namespace=None, *args, **kwargs
    ):
        super().__init__(url, token, *args, **kwargs)
        self._ocp_provider_ref = ocp_provider_ref
        self._ocp_namespace = ThreeScaleClientCRD.get_namespace(ocp_namespace)
        self._services = resources.Services(
            parent=self, instance_klass=resources.Service
        )
        self._active_docs = resources.ActiveDocs(
            parent=self, instance_klass=resources.ActiveDoc
        )
        self._policy_registry = resources.PoliciesRegistry(
            parent=self, instance_klass=resources.PolicyRegistry
        )
        self._backends = resources.Backends(
            parent=self, instance_klass=resources.Backend
        )
        self._accounts = resources.Accounts(
            parent=self, instance_klass=resources.Account
        )
        self._accounts_users = resources.AccountUsers(
            parent=self, instance_klass=resources.AccountUser
        )
        self._openapis = resources.OpenApis(
            parent=self, instance_klass=resources.OpenApi
        )
        self._tenants = resources.Tenants(parent=self, instance_klass=resources.Tenant)
        self._promotes = resources.Promotes(
            parent=self, instance_klass=resources.Promote
        )
        self._applications = resources.Applications(
            parent=self, account=None, instance_klass=resources.Application
        )
        self._app_auths = resources.AppAuths(
            parent=self, instance_klass=resources.AppAuth
        )

    @classmethod
    def get_namespace(cls, namespace):
        """
        Returns namespace. If there is no valid Openshift 'oc' session, returns "NOT LOGGED IN".
        """
        try:
            return namespace or ocp.get_project_name()
        except OpenShiftPythonException:
            return "NOT LOGGED IN"

    @property
    def services(self) -> resources.Services:
        """Gets services client
        Returns(resources.Services): Services client
        """
        return self._services

    @property
    def active_docs(self) -> resources.ActiveDocs:
        """Gets active docs client
        Returns(resources.ActiveDocs): ActiveDocs client
        """
        return self._active_docs

    @property
    def policy_registry(self) -> resources.PolicyRegistry:
        """Gets policy registry client
        Returns(resources.PolicyRegistry): Policy Registry client
        """
        return self._policy_registry

    @property
    def backends(self) -> resources.Backend:
        """Gets backend client
        Returns(resources.Backend): Backend client
        """
        return self._backends

    @property
    def accounts(self) -> resources.Accounts:
        """Gets accounts client
        Returns(resources.Accounts): Accounts client
        """
        return self._accounts

    @property
    def account_users(self) -> resources.AccountUsers:
        """Gets account users client
        Returns(resources.AccountUsers): Account Users client
        """
        return self._accounts_users

    @property
    def openapis(self) -> resources.OpenApis:
        """Gets AopenApis client
        Returns(resources.OpenApis): OpenApis client
        """
        return self._openapis

    @property
    def tenants(self) -> resources.Tenants:
        """Gets tenants client
        Returns(resources.Tenants): Tenants client
        """
        return self._tenants

    @property
    def promotes(self) -> resources.Promotes:
        """Gets promotes client
        Returns(resources.Promotes): Promotes client
        """
        return self._promotes

    @property
    def applications(self) -> resources.Applications:
        """Gets applications client
        Returns(resources.Applications): Applications client
        """
        return self._applications

    @property
    def app_auths(self) -> resources.AppAuths:
        """Gets Application Auth client
        Returns(resources.Auths): Application Auth client
        """
        return self._app_auths

    @property
    def ocp_provider_ref(self):
        """Gets provider reference"""
        return self._ocp_provider_ref

    @property
    def ocp_namespace(self):
        """Gets working namespace"""
        return self._ocp_namespace
