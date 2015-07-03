#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Author: Davide Guerri <davide.guerri@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

try:
    import shade

    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_keystone_service
version_added: "1.9"
short_description: Manage OpenStack Identity (keystone) endpoints
extends_documentation_fragment: openstack
description:
   - Manage endpoints from OpenStack.
options:
   name:
     description:
        - OpenStack service name (e.g. keystone)
     required: true
   service_type:
     description:
        - OpenStack service type (e.g. identity)
     required: true
   description:
     description:
        - Service description
     required: false
     default: Not provided
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
requirements: ["shade"]
author: Davide Guerri
'''

EXAMPLES = '''
# Add Glance service
- os_keystone_service: >
    name=glance
    service_type=image
    description="Glance image service"
    cloud: dguerri

# Delete Glance service
- os_keystone_service: >
    name=glance
    service_type=image
    description="Glance image service"
    state=absent
    cloud: dguerri
'''


def compare_services(service_a, service_b):
    return service_a['name'] == service_b['name'] and \
           service_a['type'] == service_b['service_type'] and \
           service_a['description'] == service_b['description']


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        service_type=dict(required=True),
        description=dict(required=False, default="Not provided"),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    service_name = module.params['name']
    service_type = module.params['service_type']
    service_description = module.params['description']
    state = module.params['state']

    check_mode = module.check_mode

    try:
        cloud = shade.operator_cloud(**module.params)
        service = cloud.get_service(name_or_id=service_name)
        new_service_kwargs = {
            'name': service_name,
            'service_type': service_type,
            'description': service_description
        }
        if state == "present":
            if service is None:
                if module.check_mode:
                    module.exit_json(changed=True)

                new_service = cloud.create_service(**new_service_kwargs)
                module.exit_json(changed=True,
                                 result='created',
                                 id=new_service['id'])
            elif compare_services(service, new_service_kwargs):
                module.exit_json(changed=False,
                                 result='success',
                                 id=service['id'])
            else:
                # Service already exists but something (i.e. type or desc) is
                # different.
                # Keystone v2 Services cannot be updated. And unfortunately we
                # cannot just delete and recreate them because they would
                # change their ids.
                module.exit_json(changed=False,
                                 result='exists',
                                 msg='Keystone services cannot be updated',
                                 id=service['id'])
        elif state == "absent":
            if module.check_mode:
                module.exit_json(changed=service is not None)

            if service is not None:
                cloud.delete_service(name_or_id=service_name)
                module.exit_json(changed=True, result='deleted')
            else:
                module.exit_json(changed=False, result='success')

    except shade.OpenStackCloudException as e:
        if check_mode:
            # If we have a failure in check mode
            module.exit_json(changed=True,
                             msg="exception: %s" % e)
        else:
            module.fail_json(msg="exception: %s" % e)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
