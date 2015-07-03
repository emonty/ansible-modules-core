#!/usr/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


try:
    import shade
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_user
short_description: Manage OpenStack Identity Users
extends_documentation_fragment: openstack
version_added: "2.0"
description:
    - Manage  OpenStack Identity Users
options:
   name:
     description:
        - Username for the user
     required: true
   password:
     description:
        - Password for the user
     required: true
   email:
     description:
        - Email address for the user
     required: false
     default: None
   default_project:
     description:
        - Project name or id that the user should be associated with by default
     required: false
     default: None
   domain:
     description:
        - Domain name or id to create the user in if the cloud supports domains
     required: false
     default: None
   enabled:
     description:
        - Is the user enabled
     required: false
     default: True
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a user
- os_user: name=demouser password=secret email="demo@example.com"
           description="Demo User"
'''


def main():

    argument_spec = openstack_full_argument_spec(
    argument_spec = dict(
        name=dict(required=True),
        password=dict(required=True),
        email=dict(required=False, default=None),
        default_project=dict(required=False, default=None),
        domain=dict(required=False, default=None),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params.pop('name')
    password = module.params.pop('password')
    email = module.params.pop('email')
    default_project = module.params.pop('default_project')
    domain = module.params.pop('domain')
    enabled = module.params.pop('enabled')
    state = module.params.pop('state')

    try:
        cloud = shade.openstack_cloud(**module.params)

        user = cloud.get_user(name=name)

        if state == 'present':
            if user is None:
                user = cloud.create_user(
                    name=name, password=password, email=email,
                    default_project=default_project, domain=domain,
                    enabled=enabled)
                changed = True
            else:
                if (user.name != name or user.password != password
                        or user.email != email
                        or user.default_project != default_project
                        or user.domain != default_project
                        or user.enabled != enabled):
                    cloud.update_user(
                        user.id, password=password, email=email,
                        default_project=default_project, domain=domain,
                        enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, user=user)
        elif state == 'absent':
            if user is None:
                changed=False
            else:
                cloud.delete_user(user.id)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
