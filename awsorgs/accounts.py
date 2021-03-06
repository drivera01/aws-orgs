#!/usr/bin/python


"""Manage accounts in an AWS Organization.

Usage:
  awsaccounts report [-d] [--boto-log]
  awsaccounts create (--spec-file FILE) [--exec] [-vd] [--boto-log]
  awsaccounts (-h | --help)
  awsaccounts --version

Modes of operation:
  report         Display organization status report only.
  create         Create new accounts in AWS Org per specifation.

Options:
  -h, --help                 Show this help message and exit.
  --version                  Display version info and exit.
  -s FILE, --spec-file FILE  AWS account specification file in yaml format.
  --exec                     Execute proposed changes to AWS accounts.
  -v, --verbose              Log to activity to STDOUT at log level INFO.
  -d, --debug                Increase log level to 'DEBUG'. Implies '--verbose'.
  --boto-log                 Include botocore and boto3 logs in log stream.

"""


import yaml
import time

import boto3
import botocore.exceptions
from botocore.exceptions import ClientError
import docopt
from docopt import docopt

import awsorgs
import awsorgs.orgs
from awsorgs import (
        lookup,
        get_logger,
        ensure_absent,
        get_root_id,
        validate_master_id,
)
from awsorgs.orgs import scan_deployed_accounts


def validate_account_spec_file(args):
    """
    Validate spec-file is properly formed.
    """
    spec = yaml.load(open(args['--spec-file']).read())
    string_keys = ['master_account_id']
    for key in string_keys:
        if not key in spec:
            msg = "Invalid spec-file: missing required param '%s'." % key
            raise RuntimeError(msg)
        if not isinstance(spec[key], str):
            msg = "Invalid spec-file: '%s' must be type 'str'." % key
            raise RuntimeError(msg)
    list_keys = ['accounts']
    for key in list_keys:
        if not key in spec:
            msg = "Invalid spec-file: missing required param '%s'." % key
            raise RuntimeError(msg)
        if not isinstance(spec[key], list):
            msg = "Invalid spec-file: '%s' must be type 'list'." % key
            raise RuntimeError(msg)

    # validate accounts spec
    err_prefix = "Malformed accounts spec in spec-file"
    for a_spec in spec['accounts']:
        if not isinstance(a_spec, dict):
            msg = "%s: not a dictionary: '%s'" % (err_prefix, str(a_spec))
            raise RuntimeError(msg)
        if not 'Name' in a_spec:
            msg = ("%s: missing 'Name' key near: '%s'" %
              (err_prefix, str(a_spec)))
            raise RuntimeError(msg)

    # all done!
    return spec


def scan_created_accounts(org_client):
    """
    Query AWS Organization for accounts with creation status of 'SUCCEEDED'.
    Returns a list of dictionary.
    """
    status = org_client.list_create_account_status(States=['SUCCEEDED'])
    created_accounts = status['CreateAccountStatuses']
    while 'NextToken' in status and status['NextToken']:
        status = org_client.list_create_account_status(States=['SUCCEEDED'],
                NextToken=status['NextToken'])
        created_accounts += status['CreateAccountStatuses']
    return created_accounts


def create_accounts(org_client, args, log, deployed_accounts, account_spec):
    """
    Compare deployed_accounts to list of accounts in the accounts spec.
    Create accounts not found in deployed_accounts.
    """
    for a_spec in account_spec['accounts']:
        if not lookup(deployed_accounts, 'Name', a_spec['Name'],):
            # check if it is still being provisioned
            created_accounts = scan_created_accounts(org_client)
            if lookup(created_accounts, 'AccountName', a_spec['Name']):
                log.warn("New account '%s' is not yet available" %
                        a_spec['Name'])
                break
            # create a new account
            log.info("Creating account '%s'" % (a_spec['Name']))
            if args['--exec']:
                new_account = org_client.create_account(
                        AccountName=a_spec['Name'], Email=a_spec['Email'])
                create_id = new_account['CreateAccountStatus']['Id']
                log.info("CreateAccountStatus Id: %s" % (create_id))
                # validate creation status
                counter = 0
                maxtries = 5
                while counter < maxtries:
                    creation = org_client.describe_create_account_status(
                            CreateAccountRequestId=create_id
                            )['CreateAccountStatus']
                    if creation['State'] == 'IN_PROGRESS':
                        time.sleep(5)
                        log.info("Account creation in progress for '%s'" %
                                a_spec['Name'])
                    elif creation['State'] == 'SUCCEEDED':
                        log.info("Account creation succeeded")
                        break
                    elif creation['State'] == 'FAILED':
                        log.error("Account creation failed: %s" %
                                creation['FailureReason'])
                        break
                    counter += 1
                if counter == maxtries and creation['State'] == 'IN_PROGRESS':
                     log.warn("Account creation still pending. Moving on!")


def display_provisioned_accounts(log, deployed_accounts):
    """
    Print report of currently deployed accounts in AWS Organization.
    """
    header = "Provisioned Accounts in Org:"
    overbar = '_' * len(header)
    log.info("\n%s\n%s" % (overbar, header))
    for a_name in sorted(map(lambda a: a['Name'], deployed_accounts)):
        a_id = lookup(deployed_accounts, 'Name', a_name, 'Id')
        a_email = lookup(deployed_accounts, 'Name', a_name, 'Email')
        spacer = ' ' * (24 - len(a_name))
        log.info("%s%s%s\t\t%s" % (a_name, spacer, a_id, a_email))


def main():
    args = docopt(__doc__)
    log = get_logger(args)
    org_client = boto3.client('organizations')
    root_id = get_root_id(org_client)
    deployed_accounts = scan_deployed_accounts(org_client)

    if args['--spec-file']:
        account_spec = validate_account_spec_file(args)
        validate_master_id(org_client, account_spec)

    if args['report']:
        display_provisioned_accounts(log, deployed_accounts)

    if args['create']:
        create_accounts(org_client, args, log, deployed_accounts, account_spec)
        unmanaged= [a
                for a in map(lambda a: a['Name'], deployed_accounts)
                if a not in map(lambda a: a['Name'], account_spec['accounts'])]
        if unmanaged:
            log.warn("Unmanaged accounts in Org: %s" % (', '.join(unmanaged)))


if __name__ == "__main__":
    main()
