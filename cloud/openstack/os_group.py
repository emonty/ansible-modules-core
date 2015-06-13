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
module: os_group
short_description: Manage OpenStack Identity Groups
extends_documentation_fragment: openstack
version_added: "2.0"
description:
    - Manage OpenStack Identity Groups.
options:
   name:
     description:
        - Role Name
     required: true
   description:
     description:
        - Role Description
     required: false
     default: None
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
# Create a group
- os_group: name=demo description="Demo Group"
'''


def main():

    argument_spec = openstack_full_argument_spec(
    argument_spec = dict(
        name=dict(required=True),
        description=dict(required=False, default=None),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params.pop('name')
    description = module.params.pop('description')
    state = module.params.pop('state')

    try:
        cloud = shade.openstack_cloud(**module.params)

        group = cloud.get_group(name=name)

        if state == 'present':
            if group is None:
                group = cloud.create_group(
                    name=name, description=description)
                changed = True
            else:
                if group.description != description:
                    cloud.update_group(
                        group.id, description=description)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, group=group)
        elif state == 'absent':
            if group is None:
                changed=False
            else:
                cloud.delete_group(group.id)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
