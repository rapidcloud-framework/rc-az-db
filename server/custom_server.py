#!/usr/bin/env python3

__author__ = "Jaime Zelada"
__copyright__ = "Copyright 2023, Kinect Consulting"
__license__ = "Commercial"
__email__ = "jzelada@kinect-consulting.com"

import logging
import json
import pprint

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient 
from azure.mgmt.msi import ManagedServiceIdentityClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault.keys import KeyClient

# import module
import traceback
import os
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("server")
logger.setLevel(logging.INFO)


def pp(d):
    print(pprint.pformat(d))

def get_new_token():
    tokenCredential = DefaultAzureCredential()
    scope = "https://management.core.windows.net/.default"
    access_token = tokenCredential.get_token(scope)
    return access_token.token

def get_resource_groups(params):
    # Acquire a credential object using CLI-based authentication.
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    resource_client = ResourceManagementClient(credential, subscription_id)
    group_list = resource_client.resource_groups.list()
    resource_groups = []
    sorted_entities = sorted(group_list, key=lambda x: x.name.lower(), reverse=False)
    rc_rgs = list(filter(lambda x: x.tags is not None and x.tags.get('profile') is not None and x.tags.get('profile') == params.get('env') ,sorted_entities))
    other_rgs = list(filter((lambda x: x.tags is None) ,sorted_entities))
    additional_rgs = list(filter((lambda x: x.tags is not None and x.tags.get('profile') is None) ,sorted_entities))

    final_list = rc_rgs + other_rgs + additional_rgs
    
    # for item in list(final_list):
    #     print(item.name)

    #sorted_entities = sorted(group_list, key=lambda x: x.name.lower(), reverse=False)
    for group in list(final_list):
        output_dict = {}
        is_rc = ""
        if not group.tags:
            label = f"{group.name} ({group.location})"
        else:
            if group.tags is not None:
                if group.tags.get('profile') is not None:
                    if group.tags.get('profile').lower() == params.get('env').lower():
                        is_rc = "value"
            if is_rc == '':
                label = f"{group.name} ({group.location})"
            else:
                label = f"{group.name} ({group.location}) (Managed by Rapid Cloud)"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = group.name
        output_dict['value']['scope'] = group.id
        resource_groups.append(output_dict)
    return resource_groups

def get_locations():
    # Acquire a credential object using CLI-based authentication.
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()

    subs_client = SubscriptionClient(credential)
    entities = subs_client.subscriptions.list_locations(subscription_id)

    locations = []

    for location in list(entities):
        output_dict = {}
        label = f"{location.display_name}"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = location.name
        locations.append(output_dict)
    return locations

def get_subnets_cosmosdb():
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    network_client = NetworkManagementClient(credential, subscription_id)
    vnets = network_client.virtual_networks.list_all()
    all_subnets = []
    for vnet in list(vnets):
        for subnet in vnet.subnets:
            if subnet.service_endpoints is not None:
                for endpoint in subnet.service_endpoints:
                    if endpoint.service == "Microsoft.AzureCosmosDB":
                        subnet.vnet = vnet.name
                        all_subnets.append(subnet)
                        break
    subnets = []
    for subnet in all_subnets:
        output_dict = {}
        label = f"{subnet.vnet} - {subnet.name}({subnet.address_prefix})"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = subnet.id
        subnets.append(output_dict)

    return subnets

def get_subnets_mssql():
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    network_client = NetworkManagementClient(credential, subscription_id)
    vnets = network_client.virtual_networks.list_all()
    all_subnets = []
    for vnet in list(vnets):
        for subnet in vnet.subnets:
            if subnet.service_endpoints is not None:
                for endpoint in subnet.service_endpoints:
                    if endpoint.service == "Microsoft.Sql":
                        subnet.vnet = vnet.name
                        all_subnets.append(subnet)
                        break
    subnets = []
    for subnet in all_subnets:
        output_dict = {}
        label = f"{subnet.vnet} - {subnet.name}({subnet.address_prefix})"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = subnet.id
        subnets.append(output_dict)

    return subnets

def get_mssql_servers():
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    sql_client = SqlManagementClient(credential, subscription_id)
    entities = sql_client.servers.list()

    servers = []
    for server in list(entities):
        output_dict = {}
        label = f"{server.name}"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = server.id
        servers.append(output_dict)

    return servers

def get_object_ids():
    # Acquire a credential object using CLI-based authentication.
    try:
        credential = ClientSecretCredential(client_id=os.environ["AZURE_CLIENT_ID"],client_secret=os.environ["AZURE_CLIENT_SECRET"],tenant_id=os.environ["AZURE_TENANT_ID"])
        graph_client = GraphClient(credential=credential)
        users = graph_client.get('/users?$select=displayName,id')
        service_principal = graph_client.get('/applications?$select=displayName,id')
        entities_users = json.dumps(users.json())
        ent_users = json.loads(entities_users)

    except Exception as e:
        traceback.print_exc()
    #For the users 
    users = []
    for user in list(ent_users.get('value')):
        output_dict = {}
        #print(user.get('displayName'))
        label = f"{user.get('displayName')}"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = user.get('id')
        users.append(output_dict)
    return users

def get_identities():
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    msi_client = ManagedServiceIdentityClient(credential, subscription_id)
    entities = msi_client.user_assigned_identities.list_by_subscription()

    users = []
    for user in list(entities):
        output_dict = {}
        label = f"{user.name}"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = user.id
        users.append(output_dict)

    return users

def get_kv_keys():
    # Acquire a credential object using CLI-based authentication.
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    kv_client = KeyVaultManagementClient(credential,subscription_id)
    entities = kv_client.vaults.list_by_subscription()

    allkeys = []
    keys = []

    for keyvault in list(entities):
        # print(keyvault)
        try:
            key_client = KeyClient(keyvault.properties.vault_uri, DefaultAzureCredential())
            kv_keys = key_client.list_properties_of_keys()
            for key in list(kv_keys):
                key_versions = key_client.list_properties_of_key_versions(key.name)
                versions = []
                for key_version in list(key_versions):
                    versions.append(key_version)
                key.last_version = versions[-1].version
                allkeys.append(key)
        except Exception as e:
            # print(f"custom_server.py error: {e}")
            continue
    
    for key in list(allkeys):
        output_dict = {}
        label = f"{key.name}"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = f"{key.id}/{key.last_version}"
        keys.append(output_dict)
    return keys

def get_unversioned_kv_keys():
    # Acquire a credential object using CLI-based authentication.
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    credential = DefaultAzureCredential()
    kv_client = KeyVaultManagementClient(credential,subscription_id)
    entities = kv_client.vaults.list_by_subscription()

    allkeys = []
    keys = []

    for keyvault in list(entities):
        # print(keyvault)
        kv_id = keyvault.id
        try:
            key_client = KeyClient(keyvault.properties.vault_uri, DefaultAzureCredential())
            kv_keys = key_client.list_properties_of_keys()
            for key in list(kv_keys):
                key_versions = key_client.list_properties_of_key_versions(key.name)
                versions = []
                for key_version in list(key_versions):
                    versions.append(key_version)
                # key.last_version = versions[-1].version
                # key.vault_url = versions[-1]
                key.vault_id = kv_id
                allkeys.append(key)
        except Exception as e:
            # print(f"custom_server.py error: {e}")
            continue

    keys = []
    for key in list(allkeys):
        output_dict = {}
        label = f"{key.name}"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = f"{key.vault_id}|{key.name}"
        keys.append(output_dict)
    return keys

def get_managed_identities():
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    token = get_new_token()
    api_call_headers = {'Authorization': 'Bearer ' + token}
    response = requests.get(f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.ManagedIdentity/userAssignedIdentities?api-version=2023-01-31",
                            headers=api_call_headers, verify=False)

    identities = []

    response2 = json.loads(response.text)
    for identity in response2['value']:
        output_dict = {}
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = identity['name']
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = identity['id']
        identities.append(output_dict)
    return identities

def custom_endpoint(action, params, boto3_session, user_session):
    if action == "resource_groups":
        return get_resource_groups(params)
    elif action == "locations":
        return get_locations()
    elif action == "subnets":
        return get_subnets_cosmosdb()
    elif action == "subnets_mssql":
        return get_subnets_mssql()
    elif action == "mssql_servers":
        return get_mssql_servers()
    elif action == "users":
        return get_object_ids()
    elif action == "identities":
        return get_identities()
    elif action == "keys":
        return get_kv_keys()
    elif action == "unversioned_keys":
        return get_unversioned_kv_keys()
    elif action == "managedidentities":
        return get_managed_identities()
    else:
        pp(f"no such endpoint: {action}")
        return ["no such endpoint"]

    return []
