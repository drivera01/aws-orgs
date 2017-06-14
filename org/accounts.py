#!/usr/bin/python

import boto3
from botocore.exceptions import (NoCredentialsError, ClientError)
import inspect
from org import (client,find_in_dictlist)



#
# Account functions
#

def scan_deployed_accounts():
    """
    Query AWS Organization for successfully created accounts.
    Returns a list of dictionary.
    """
    deployed_accounts = []
    created_accounts = client.list_create_account_status(
        States=['SUCCEEDED']
    )['CreateAccountStatuses']
    for account_id in map(lambda a: a['AccountId'], created_accounts):
        deployed_accounts.append( client.describe_account(AccountId=account_id)['Account'] )
    return deployed_accounts



def get_account_id_by_name(deployed_accounts, account_name):
    """
    search 'deployed_accounts' dictlist for 'account_name'. return the
    acccount Id or 'None'.
    """
    return find_in_dictlist(deployed_accounts, 'Name', account_name, 'Id')


def get_account_email_by_name(deployed_accounts, account_name):
    """
    search 'deployed_accounts' dictlist for 'account_name'. return the
    acccount Email or 'None'.
    """
    return find_in_dictlist(deployed_accounts, 'Name', account_name, 'Email')


def get_parent_id(account_id):
    """
    Query deployed AWS organanization for 'account_id. Return the
    'Id' of the parent OrganizationalUnit or 'None'.
    """
    parents = client.list_parents(ChildId=account_id)['Parents']
    if len(parents) == 1:
        return parents[0]['Id']
    else:
        #handle error
        #print 'account', account_id, 'has more than one parent', parents
        return None


def list_accounts_in_ou (ou_id):
    """
    Query deployed AWS organanization for accounts contained in
    OrganizationalUnit ('ou_id').  Return a list of accounts
    (list of type dict).
    """
    account_list = client.list_accounts_for_parent(
        ParentId=ou_id
    )['Accounts']
    return sorted(map(lambda a: a['Name'], account_list))


def create_account(account_spec):
    """
    Create a new account in AWS Organization based on 'account_spec'.
    """
    return client.create_account(
        AccountName=a_spec['Name'],
        Email=a_spec['Email']
    )['CreateAccountStatus']['State']


def move_account(account_id, parent_id, target_id):
    """
    Alter deployed AWS organanization. Move account referenced by
    'account_id' out of current containing OU ('parent_id') and
    into target OU ('target_id')
    """
    client.move_account(
        AccountId=account_id,
        SourceParentId=parent_id,
        DestinationParentId=target_id
    )
    # handle exception


def display_provissioned_accounts(deployed_accounts):
    """
    Print report of currently deployed accounts in AWS Organization.
    """
    print
    print "_____________________________"
    print "Provissioned Accounts in Org:"
    for a_name in sorted(map(lambda a: a['Name'], deployed_accounts)):
        a_id = get_account_id_by_name(deployed_accounts, a_name)
        a_email = get_account_email_by_name(deployed_accounts, a_name)
        print "Name:\t\t%s\nEmail:\t\t%s\nId:\t\t%s\n" % (a_name, a_email, a_id)

