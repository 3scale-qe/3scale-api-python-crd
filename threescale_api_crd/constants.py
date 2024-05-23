"""
Module with constants.
"""

SERVICE_AUTH = {"userkey": "1", "appKeyAppID": "2", "oidc": "oidc"}

SERVICE_AUTH_DEFS = {
    "1": {
        "userkey": {
            #  "token", see https://issues.redhat.com/browse/THREESCALE-11072
            "authUserKey": "user_key",
            "credentials": "authorization",
            "gatewayResponse": {},
        },
    },
    "2": {
        "appKeyAppID": {
            "appID": "app_id",
            "appKey": "app_key",
            "credentials": "authorization",
            "gatewayResponse": {},
        },
    },
    "oidc": {
        "oidc": {
            "issuerEndpoint": " ",
            "issuerType": "keycloak",
            "authenticationFlow": {
                "standardFlowEnabled": False,
                "implicitFlowEnabled": False,
                "serviceAccountsEnabled": False,
                "directAccessGrantsEnabled": True,
            },
            "jwtClaimWithClientID": None,
            "jwtClaimWithClientIDType": None,
            "credentials": "authorization",
            "gatewayResponse": {},
        },
    },
}

SPEC_SERVICE = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "Product",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "name": None,
        "providerAccountRef": {
            "name": None,
        },
        "systemName": None,
        "description": None,
        "deployment": {
            "apicastHosted": {
                "authentication": {
                    "userkey": {
                        #  "token", see https://issues.redhat.com/browse/THREESCALE-11072
                        "authUserKey": "user_key",
                        "credentials": "query",
                        "gatewayResponse": {},
                    },
                },
            },
        },
        "applicationPlans": {
            "AppPlanTest": {
                "setupFee": "0.00",
                "costMonth": "0.00",
                "published": True,
            }
        },
    },
    "policies": [],
}

SPEC_PROXY = {}


SPEC_BACKEND = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "Backend",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "name": None,
        "privateBaseURL": None,
        "systemName": None,
        "providerAccountRef": {
            "name": None,
        },
        "description": None,
    },
}

SPEC_MAPPING_RULE = {
    "spec": {
        "httpMethod": None,
        "pattern": None,
        "increment": None,
        "metricMethodRef": None,
        "last": None,
    }
}

SPEC_BACKEND_USAGE = {
    "spec": {
        "path": None,
    }
}

SPEC_LIMIT = {
    "spec": {
        "period": None,
        "value": None,
        "metricMethodRef": None,
    }
}

SPEC_PRICING_RULE = {
    "spec": {
        "from": None,
        "to": None,
        "pricePerUnit": None,
        "metricMethodRef": None,
    }
}

SPEC_METRIC = {
    "spec": {
        "friendlyName": None,
        "unit": None,
        "description": None,
    }
}

SPEC_APP_PLANS = {
    "spec": {
        "name": None,
        "appsRequireApproval": None,
        "trialPeriod": None,
        "setupFee": None,
        "costMonth": None,
        "published": True,
        "pricingRules": None,
        "limits": None,
    }
}

SPEC_ACTIVE_DOC = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "ActiveDoc",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "name": None,
        "providerAccountRef": {
            "name": None,
        },
        "activeDocOpenAPIRef": {
            "secretRef": "oas3-json-secret",
        },
        "systemName": None,
        "description": None,
        "productSystemName": None,
        "published": False,
        "skipSwaggerValidations": False,
    },
}

SPEC_POLICY_REG = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "CustomPolicyDefinition",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "name": None,
        "providerAccountRef": {
            "name": None,
        },
        "version": None,
        "schema": {
            "name": None,
            "version": None,
            "summary": None,
            "$schema": None,
            "description": None,
            "configuration": None,
        },
    },
}


SPEC_ACCOUNT = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "DeveloperAccount",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "providerAccountRef": {
            "name": None,
        },
        "orgName": None,
        "monthlyBillingEnabled": None,
        "monthlyChargingEnabled": None,
    },
}

SPEC_ACCOUNT_USER = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "DeveloperUser",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "providerAccountRef": {
            "name": None,
        },
        "username": None,
        "email": None,
        "suspended": None,
        "role": None,
        "passwordCredentialsRef": {
            "name": None,
        },
        "developerAccountRef": {
            "name": None,
        },
    },
}

SPEC_POLICY = {
    "spec": {
        "name": None,
        "version": None,
        "enabled": None,
        "configuration": {},
    }
}


SPEC_OPEN_API = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "OpenAPI",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "providerAccountRef": {
            "name": None,
        },
    },
}


SPEC_TENANT = {
    "apiVersion": "capabilities.3scale.net/v1alpha1",
    "kind": "Tenant",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "organizationName": None,
        "email": None,
        "username": "admin",
        "systemMasterUrl": None,
        "masterCredentialsRef": {
            "name": None,
        },
        "passwordCredentialsRef": {
            "name": None,
        },
        "tenantSecretRef": {"name": None, "namespace": None},
    },
}

SPEC_PROMOTE = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "ProxyConfigPromote",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "providerAccountRef": {
            "name": None,
        },
        "productCRName": None,
    },
}

SPEC_APP_AUTH = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "ApplicationAuth",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "providerAccountRef": {
            "name": None,
        },
        "applicationCRName": None,
        "generateSecret": False,
        "authSecretRef": {
            "name": None,
        },
    },
}

SPEC_APPLICATION = {
    "apiVersion": "capabilities.3scale.net/v1beta1",
    "kind": "Application",
    "metadata": {
        "name": None,
        "namespace": None,
        "annotations": {"insecure_skip_verify": "true"},
    },
    "spec": {
        "name": None,
        "providerAccountRef": {
            "name": None,
        },
        "description": None,
        "accountCR": {
            "name": None,
        },
        "productCR": {
            "name": None,
        },
        "applicationPlanName": None,
        "suspend": False,
    },
}

SPEC_METHOD = {
    "spec": {
        "friendlyName": None,
        "description": None,
    }
}

KEYS_SERVICE = {
    "description": "description",
    "name": "name",
    "system_name": "systemName",
    "mapping_rules": "mappingRules",
    "metrics": "metrics",
    "backend_usages": "backendUsages",
    "application_plans": "applicationPlans",
    "deployment": "deployment",
    "policies": "policies",
    "methods": "methods",
}

KEYS_PROXY_RESPONSES = {
    "error_auth_failed": "errorAuthFailed",
    "error_auth_missing": "errorAuthMissing",
    "error_headers_auth_failed": "errorHeadersAuthFailed",
    "error_headers_auth_missing": "errorHeadersAuthMissing",
    "error_headers_limits_exceeded": "errorHeadersLimitsExceeded",
    "error_headers_no_match": "errorHeadersNoMatch",
    "error_limits_exceeded": "errorLimitsExceeded",
    "error_no_match": "errorNoMatch",
    "error_status_auth_failed": "errorStatusAuthFailed",
    "error_status_auth_missing": "errorStatusAuthMissing",
    "error_status_limits_exceeded": "errorStatusLimitsExceeded",
    "error_status_no_match": "errorStatusNoMatch",
}

KEYS_PROXY_SECURITY = {
    "secret_token": "secretToken",
    "hostname_rewrite": "hostHeader",
}

KEYS_PROXY = {
    "auth_app_id": "appID",
    "auth_app_key": "appKey",
    "auth_user_key": "authUserKey",
    "credentials_location": "credentials",
    "endpoint": "productionPublicBaseURL",
    "jwt_claim_with_client_id": "jwtClaimWithClientID",
    "jwt_claim_with_client_id_type": "jwtClaimWithClientIDType",
    "oidc_issuer_endpoint": "issuerEndpoint",
    "oidc_issuer_type": "issuerType",
    "sandbox_endpoint": "stagingPublicBaseURL",
}

KEYS_OIDC = {
    "standard_flow_enabled": "standardFlowEnabled",
    "implicit_flow_enabled": "implicitFlowEnabled",
    "service_accounts_enabled": "serviceAccountsEnabled",
    "direct_access_grants_enabled": "directAccessGrantsEnabled",
}

KEYS_BACKEND = {
    "description": "description",
    "name": "name",
    "system_name": "systemName",
    "mapping_rules": "mappingRules",
    "private_endpoint": "privateBaseURL",
    "metrics": "metrics",
}
KEYS_MAPPING_RULE = {
    "http_method": "httpMethod",
    "pattern": "pattern",
    "delta": "increment",
    "metric_id": "metricMethodRef",
    "last": "last",
}
KEYS_ACTIVE_DOC = {
    "system_name": "systemName",
    "name": "name",
    "description": "description",
    "published": "published",
    "skip_swagger_validations": "skipSwaggerValidations",
    "service_id": "productSystemName",
    # because of modify function for update
    "activeDocOpenAPIRef": "activeDocOpenAPIRef",
}

KEYS_POLICY_REG = {
    "name": "name",
    "version": "version",
    "schema": "schema",
    "summary": "summary",
    "$schema": "$schema",
    "description": "description",
    "configuration": "configuration",
}

KEYS_METRIC = {
    "description": "description",
    "unit": "unit",
    "friendly_name": "friendlyName",
    "system_name": "system_name",
}

KEYS_LIMIT = {
    "period": "period",
    "value": "value",
    # 'metric_name': 'metricMethodRef', should be processed
}

KEYS_APP_PLANS = {
    "name": "name",
    "approval_required": "appsRequireApproval",
    "trial_period_days": "trialPeriod",
    "setup_fee": "setupFee",
    "cost_per_month": "costMonth",
    "state_event": "published",
    "system_name": "system_name",
    "limits": "limits",
    "pricingRules": "pricingRules",
    # missing state, cancellation_period, default, custom
}

KEYS_BACKEND_USAGE = {
    "path": "path",
    "service_id": "service_id",
    "backend_id": "backend_id",
}

KEYS_ACCOUNT = {
    "org_name": "orgName",
    "monthly_billing_enabled": "monthlyBillingEnabled",
    "monthly_charging_enabled": "monthlyChargingEnabled",
    # missing credit_card_stored, created_at, updated_at
}

KEYS_ACCOUNT_USER = {
    "username": "username",
    "email": "email",
    "suspended": "suspended",
    "role": "role",
}

KEYS_POLICY = {
    "name": "name",
    "version": "version",
    "configuration": "configuration",
    "enabled": "enabled",
}

KEYS_OPEN_API = {
    "productionPublicBaseURL": "productionPublicBaseURL",
    "stagingPublicBaseURL": "stagingPublicBaseURL",
    "productSystemName": "productSystemName",
    "privateBaseURL": "privateBaseURL",
    "prefixMatching": "prefixMatching",
    "privateAPIHostHeader": "privateAPIHostHeader",
    "privateAPISecretToken": "privateAPISecretToken",
    "oidc": "oidc",
}

KEYS_OPEN_API_OIDC = {
    "issuerEndpoint": "issuerEndpoint",
    "issuerEndpointRef": "issuerEndpointRef",
    "issuerType": "issuerType",
    "authenticationFlow": "authenticationFlow",
    "jwtClaimWithClientID": "jwtClaimWithClientID",
    "jwtClaimWithClientIDType": "jwtClaimWithClientIDType",
    "credentials": "credentials",
    "gatewayResponse": "gatewayResponse",
}

KEYS_TENANT = {
    "org_name": "organizationName",
    "email": "email",
    "username": "username",
    "system_master_url": "systemMasterUrl",
    "tenantSecretRef": "tenantSecretRef",
    "passwordCredentialsRef": "passwordCredentialsRef",
    "masterCredentialsRef": "masterCredentialsRef",
}

KEYS_LIMIT = {
    "period": "period",
    "value": "value",
    "metricMethodRef": "metricMethodRef",
}

KEYS_PRICING_RULE = {
    "cost_per_unit": "pricePerUnit",
    "min": "from",
    "max": "to",
    "metricMethodRef": "metricMethodRef",
}

KEYS_PROMOTE = {
    "productCRName": "productCRName",
    "production": "production",
    "deleteCR": "deleteCR",
}

KEYS_APP_AUTH = {
    "applicationCRName": "applicationCRName",
    "generateSecret": "generateSecret",
    "authSecretRef": "authSecretRef",
}

KEYS_APPLICATION = {
    "description": "description",
    "name": "name",
    "plan_name": "applicationPlanName",
    "suspend": "suspend",
    "service_name": "productCR",
    "account_name": "accountCR",
}

KEYS_METHOD = {
    "description": "description",
    "friendly_name": "friendlyName",
    "system_name": "system_name",
}

SPEC_SECRET = {
    "kind": "Secret",
    "apiVersion": "v1",
    "metadata": {
        "name": None,
        "namespace": None,
    },
    "data": {},
    "type": "Opaque",
}
