
#
# OrganizaionalUnit functions
#

def children_in_ou_spec(ou_spec):
    """
    Check if if 'ou_spec' has any child OU.  Returns boolean.
    """
    if 'OU' in ou_spec and ou_spec['OU'] != None and len(ou_spec['OU']) != 0:
        return True
    return False


def get_ou_id_by_name(ou_name):
    """
    search 'deployed_ou' dictlist for 'ou_name'. return the
    OrganizationalUnit Id or 'None'.
    """
    return find_in_dictlist(deployed_ou, 'Name', ou_name, 'Id')


# return ou name from an ou id
def get_ou_name_by_id(ou_id):
    """
    Search 'deployed_ou' dictlist for 'ou_id'. Return the OrganizationalUnit
    Name or 'None'.  If ou_id is the root_id, return 'root'.
    """
    if ou_id == root_id:
        return 'root'
    else:
        return find_in_dictlist(deployed_ou, 'Id', ou_id, 'Name')


def create_ou (parent_id, ou_name):
    """
    Create new OrganizationalUnit ('ou_name') under specified parent
    OU ('parent_id')
    """
    return org_client.create_organizational_unit(
        ParentId=parent_id,
        Name=ou_name
    )['OrganizationalUnit']



def delete_ou (ou_name):
    """
    Delete named OrganizaionalUnit from deployed AWS Organization.  Check if
    any children OU exist first.
    """
    if len(ou_table[ou_name]['Children']) > 0:
        print "OU %s has children. Can not delete." % ou_name
    else:
        org_client.delete_organizational_unit (
            OrganizationalUnitId=ou_table[ou_name]['Id']
        )


def display_provissioned_ou (parent_name, parent_id, indent):
    """
    Recursive function to display the deployed AWS Organization structure.
    """
    # query aws for child orgs
    child_ou_list = org_client.list_children(
        ParentId=parent_id,
        ChildType='ORGANIZATIONAL_UNIT'
    )['Children']
    # print parent ou name
    tab = '  '
    print tab*indent + parent_name + ':'
    # look for policies
    policy_names = list_policies_in_ou(parent_id)
    if len(policy_names) > 0:
        print tab*indent + tab + 'policies: ' + ', '.join(policy_names)
    # look for accounts
    account_list = list_accounts_in_ou(parent_id)
    if len(account_list) > 0:
        print tab*indent + tab + 'accounts: ' + ', '.join(account_list)
    # look for child OUs
    if len(child_ou_list ) > 0:
        print tab*indent + tab + 'child_ou:'
        indent+=2
        for ou in child_ou_list:
            # recurse
            display_provissioned_ou(get_ou_name_by_id(ou['Id']), ou['Id'], indent)


def manage_policy_attachments(ou_spec, ou_id):
    """
    Attach or detach specified Service Control Policy ('ou_spec') to a
    deployed OrganizatinalUnit ('ou_id)'.
    """
    global change_counter
    # attach specified policies
    p_spec = get_policy_spec_for_ou(ou_spec)
    for policy_name in p_spec:
        policy_id = get_policy_id_by_name(policy_name)

        if not policy_attached(policy_id, ou_id) and not ensure_absent(ou_spec):
            change_counter += 1
            if not args.silent:
                print "attaching policy %s to OU %s" % (policy_name, ou_spec['Name'])
            if not args.dry_run:
                attach_policy(policy_id, ou_id)

    # detach unspecified policies
    policy_list = list_policies_in_ou(ou_id)
    for policy_name in policy_list:
        if policy_name not in p_spec and not ensure_absent(ou_spec):
            change_counter += 1
            policy_id = get_policy_id_by_name(policy_name)
            if not args.silent:
                print "detaching policy %s from OU %s" % (policy_name, ou_spec['Name'])
            if not args.dry_run:
                detach_policy(policy_id, ou_id)
