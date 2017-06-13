#!/usr/bin/python

"""
a module to manage AWS Organizations
"""

import boto3
#import yaml
#import json
import sys
import os
#import argparse
from botocore.exceptions import (NoCredentialsError, ClientError)
import inspect




def get_root_id():
    """
    Query deployed AWS Organization for its Root ID.
    """
    try:
        root_id = org_client.list_roots()['Roots'][0]['Id']
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
    p_type = org_client.describe_organization()['Organization']['AvailablePolicyTypes'][0]
    if p_type['Type'] == 'SERVICE_CONTROL_POLICY' and p_type['Status'] != 'ENABLED':
        org_client.enable_policy_type(
            RootId=root_id,
            PolicyType='SERVICE_CONTROL_POLICY'
        )



def build_deployed_ou_table(parent_name, parent_id, deployed_ou):
    """
    Recursively travers deployed AWS Organization.  Build the 'deployed_ou'
    lookup table (list of dict).
    """
    children_ou = org_client.list_organizational_units_for_parent(
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

    global org_client, root_id, deployed_accounts, deployed_policies, deployed_ou
    
    # set up aws client for orgs
    org_client = boto3.client('organizations')

    # determine the Organization Root ID
    root_id = get_root_id()
    
    # kinda does what it says
    enable_policy_type_in_root(root_id)
    
    # Scan deployed AWS Organization resources and build lookup 
    # tables - lists of dictionaries.
    deployed_accounts = org_client.list_accounts()['Accounts']
    deployed_policies = org_client.list_policies(
        Filter='SERVICE_CONTROL_POLICY'
    )['Policies']
    
    deployed_ou = []
    ou_table = {}
    build_deployed_ou_table('root', root_id, deployed_ou)



