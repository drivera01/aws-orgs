________
aws-orgs
________

This project is an attempt to provision AWS Oranizations IAM resources
based on structured imput files.

aws-orgs installation provides three python executibles:  

awsorgs
    Manage recources in an AWS Organization.

awsaccounts
    Manage accounts in an AWS Organization.

awsauth
    Manage users, group, and roles for cross account access
    in an AWS Organization.



Run each of these with the '--help' option for usage documentation.

See the ``samples/`` directory for anotated examples of spec-file syntax.


**Installation** (as editable local project)::

  git clone https://github.com/ashleygould/aws-orgs
  pip install --user -e aws-orgs/


**Uninstall**::

  pip uninstall aws-orgs
  rm ~/.local/bin/{awsorgs,awsaccounts,awsauth}
  
  **NOTE** Individual users .bash_profile **must** include the reference $HOME/.local in the path
    PATH=$PATH:$HOME/.local/bin:$HOME/bin
