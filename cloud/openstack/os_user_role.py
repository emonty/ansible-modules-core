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
module: os_user_role
short_description: Associate OpenStack Identity users and roles
extends_documentation_fragment: openstack
version_added: "2.0"
description:
    - Grant and revoke roles in either project or domain context for
      OpenStack Identity Users
options:
   role:
     description:
        - Name or id for the role
     required: true
   user:
     description:
        - Name or id for the user. (user or group required)
     required: true
   group:
     description:
        - Name or id for the group. (user or group required)
     required: true
   project:
     description:
        - Name or id of the project to scope the role assocation to.
     required: false
     default: None
   domain:
     description:
        - Name or id of the domain to scope the role association to.
     required: false
     default: None
   state:
     description:
       - Should the roles be present or absent on the user
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Grant an admin role on the user admin in the project project1
- os_user_role: user=admin role=admin project=project1 domain=default
# Revoke the awesome role from the user barney in the newyork domain
- os_user_role: user=barney role=awesome domain=newyork state=absent
'''


def main():

    argument_spec = openstack_full_argument_spec(
    argument_spec = dict(
        role=dict(required=True),
        user=dict(required=True),
        group=dict(required=True),
        project=dict(required=False, default=None),
        domain=dict(required=False, default=None),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module_kwargs = openstack_module_kwargs(
        required_one_of=[
            ['user', 'group']
        ])
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    role = module.params.pop('role')
    user = module.params.pop('user')
    group = module.params.pop('group')
    project = module.params.pop('project')
    domain = module.params.pop('domain')
    state = module.params.pop('state')

    try:
        cloud = shade.openstack_cloud(**module.params)

        params = {}
        if user:
            params['user'] = cloud.get_user(user).id
        if group:
            params['group'] = cloud.get_group(group).id
        if project:
            params['project'] = cloud.get_project(project).id
        if domain:
            params['domain'] = cloud.get_domain(domain).id
        assignment = cloud.get_role_assignment(role, filters=params)

        if state == 'present':

            if assignment:
                changed = False
            else:
                cloud.grant_role(
                    role_name_or_id=role,
                    user_name_or_id=user,
                    domain_name_or_id=domain,
                    project_name_or_id=project)
                changed = True
        elif state == 'absent':
            if assignment:
                cloud.revoke_role(
                    role_name_or_id=role,
                    user_name_or_id=user,
                    domain_name_or_id=domain,
                    project_name_or_id=project)
                changed=True
            else:
                changed=False
        module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
