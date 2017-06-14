#!/usr/bin/python

import boto3
from botocore.exceptions import (NoCredentialsError, ClientError)
import inspect
from org import (client,find_in_dictlist)


#
# Policy functions
#

def scan_deployed_policies():
    """
    Query AWS Organization for deployed Service Control Policies.
    Returns a list of dictionary.
    """
    return client.list_policies(
        Filter='SERVICE_CONTROL_POLICY'
    )['Policies']


def get_policy_id_by_name(deployed_policies, policy_name):
    """
    search 'deployed_policies' dictlist for 'policy_name'. return the
    policy Id or 'None'.
    """
    return find_in_dictlist(deployed_policies, 'Name', policy_name, 'Id')


def get_policy_description(deployed_policies, policy_id):
    """
    Search 'deployed_policies' dictlist for 'policy_id'. Return the
    policy Description or 'None'.
    """
    return find_in_dictlist(deployed_policies, 'Id', policy_id, 'Description')


def get_policy_content(policy_id):
    """
    Query deployed AWS Organization.  Return the policy content
    (json string) accociated with the Service Control Policy
    referenced by 'policy_id'.
    """
    return client.describe_policy(PolicyId=policy_id)['Policy']['Content']


def list_policies_in_ou (ou_id):
    """
    Query deployed AWS organanization.  Return a list (of type dict)
    of policies attached to OrganizationalUnit referenced by 'ou_id'.
    """
    policies_in_ou = client.list_policies_for_target(
        TargetId=ou_id,
        Filter='SERVICE_CONTROL_POLICY',
    )['Policies']
    return sorted(map(lambda ou: ou['Name'], policies_in_ou))


def get_policy_spec_for_ou(ou_spec):
    """
    Search 'ou_spec' dict for a list of policy names specified for
    attachment to this OrganizationalUnit.  Prepend the 'default_policy'
    to this list and return list.
    """
    if 'Policy' in ou_spec and ou_spec['Policy'] != None:
        return [default_policy] + ou_spec['Policy']
    else:
        return [default_policy]


def specify_policy_content(p_spec):
    """
    Compose and return (as json string) a policy content specification as
    per the given policy spec ('p_spec').
    """
    return """{ "Version": "2012-10-17", "Statement": [ { "Effect": "%s", "Action": %s, "Resource": "*" } ] }""" % (p_spec['Effect'], json.dumps(p_spec['Actions']))


def create_policy(p_spec):
    """
    Create a new Service Control Policy in the AWS Organization based on
    a policy specification ('p_spec').
    """
    client.create_policy (
        Content=specify_policy_content(p_spec),
        Description=p_spec['Description'],
        Name=p_spec['Name'],
        Type='SERVICE_CONTROL_POLICY'
    )


def update_policy( p_spec, policy_id ):
    """
    Update a deployed Service Control Policy ('policy_id') in the
    AWS Organization based on a policy specification ('p_spec').
    """
    client.update_policy(
        PolicyId=policy_id,
        Content=specify_policy_content(p_spec),
        Description=p_spec['Description'],
    )


def delete_policy(policy_id):
    """
    Delete a deployed Service Control Policy ('policy_id') in the
    AWS Organization.
    """
    client.delete_policy(PolicyId=policy_id)


def policy_attached(policy_id, ou_id,):
    """
    Test if a deployed Service Control Policy ('policy_id') is attached to
    a given OrganizationalUnit ('ou_id').  Returns a boolean.
    """
    policy_targets = client.list_targets_for_policy (
        PolicyId=policy_id
    )['Targets']
    if ou_id in map(lambda ou: ou['TargetId'], policy_targets):
        return True
    return False


def attach_policy (policy_id, ou_id,):
    """
    Attach a deployed Service Control Policy ('policy_id') to a given
    OrganizationalUnit ('ou_id').
    """
    client.attach_policy (
        PolicyId=policy_id,
        TargetId=ou_id
    )


def detach_policy (policy_id, ou_id,):
    """
    Detach a deployed Service Control Policy ('policy_id') from a given
    OrganizationalUnit ('ou_id').
    """
    client.detach_policy (
        PolicyId=policy_id,
        TargetId=ou_id
    )


def display_provissioned_policies(deployed_policies):
    """
    Print report of currently deployed Service Control Policies in
    AWS Organization.
    """
    print
    print "______________________________________"
    print "Provissioned Service Control Policies:"
    for policy in deployed_policies:
        print "Name:\t\t%s\nDescription:\t%s\nId:\t\t%s" % (
            policy['Name'],
            policy['Description'],
            policy['Id']
        )
        print "Content:\t%s\n" % get_policy_content(policy['Id'])

