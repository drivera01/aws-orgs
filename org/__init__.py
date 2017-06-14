#!/usr/bin/python

"""
a module to manage AWS Organizations
"""

import boto3
from botocore.exceptions import (NoCredentialsError, ClientError)
import inspect
import yaml
import json




def get_root_id():
    """
    Query deployed AWS Organization for its Root ID.
    """
    try:
        root_id = client.list_roots()['Roots'][0]['Id']
        return root_id
    except NoCredentialsError as e:
        print e
        print "at function:", inspect.getframeinfo(inspect.currentframe())[2]
        print "in module:", __name__
        raise SystemExit
    except ClientError as e:
        print e
        print "at function:", inspect.getframeinfo(inspect.currentframe())[2]
        print "in module:", __name__
        raise SystemExit



def enable_policy_type_in_root(root_id):
    """
    ensure policy type 'SERVICE_CONTROL_POLICY' is enabled in the
    organization root.
    """
    p_type = client.describe_organization()['Organization']['AvailablePolicyTypes'][0]
    if p_type['Type'] == 'SERVICE_CONTROL_POLICY' and p_type['Status'] != 'ENABLED':
        client.enable_policy_type(
            RootId=root_id,
            PolicyType='SERVICE_CONTROL_POLICY'
        )



def parse_org_specification(args):
    """
    load yaml 'spec-file' into dictionary.
    set global vars:
        org_spec
        default_policy
        master_account
    """
    global org_spec, default_policy, master_account
    org_spec = yaml.load(args.spec_file.read())
    for policy in org_spec['policy_spec']:
        if 'Default' in policy and policy['Default'] == True:
            default_policy = policy['Name']
    for account in org_spec['account_spec']:
        if 'Master' in account and account['Master'] == True:
            master_account = account['Name']


def ensure_absent(spec):
    """
    test if an 'Ensure' key is set to absent in dictionary 'spec'
    """
    if 'Ensure' in spec and spec['Ensure'] == 'absent':
        return True
    else:
        return False


def find_in_dictlist (dictlist, searchkey, searchvalue, returnkey):
    """
    Find a value in a list of dictionaries based on a known key:value.
    Return found value or 'None'.

    args:
        dictlist:    data structure to search -  a list of type dictionary.
        seachkey:    name of key to use as search criteria
        seachvalue:  value to use as search criteria
        returnkey:   name of key indexing the value to return
    """

    # make sure keys exist
    if not filter(lambda d: searchkey in d and returnkey in d, dictlist):
        #error: key not found
        return None

    # check for duplicate search values
    values = map(lambda d: d[searchkey], dictlist)
    if len(values) != len(set(values)):
        # error: duplicate search values
        return None

    # find the matching dictionary and return the indexed value
    result = filter(lambda d: d[searchkey] == searchvalue, dictlist)
    if len(result) == 1:
        return result[0][returnkey]
    else:
        return None




def build_deployed_ou_table(parent_name, parent_id, deployed_ou):
    """
    Recursively travers deployed AWS Organization.  Build the 'deployed_ou'
    lookup table (list of dict).
    """
    children_ou = client.list_organizational_units_for_parent(
        ParentId=parent_id
    )['OrganizationalUnits']

    for ou in children_ou:
        ou['ParentId'] = parent_id
        deployed_ou.append(ou)
        build_deployed_ou_table(ou['Name'], ou['Id'], deployed_ou)

    if not parent_name in map(lambda ou: ou['Name'], deployed_ou):
        deployed_ou.append({
            'Name':parent_name,
            'Id': parent_id,
            'Children': map(lambda ou: ou['Name'], children_ou),
        })




def init_vars():
    """
    Initialize global vars
    """

    global client, root_id, deployed_accounts, deployed_policies, deployed_ou
    

    # determine the Organization Root ID
    root_id = get_root_id()
    
    # kinda does what it says
    enable_policy_type_in_root(root_id)
    
    # Scan deployed AWS Organization resources and build lookup 
    # tables - lists of dictionaries.
    
    deployed_ou = []
    build_deployed_ou_table('root', root_id, deployed_ou)



# set up aws client for orgs
client = boto3.client('organizations')
