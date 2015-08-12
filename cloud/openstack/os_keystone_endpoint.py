#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Author: Davide Guerri <davide.guerri@hp.com>
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

    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_keystone_endpoint
version_added: "1.9"
short_description: Manage OpenStack Identity (Keystone v2) endpoints
extends_documentation_fragment: openstack
description:
   - Manage endpoints from OpenStack.
options:
   service_name:
     description:
        - |
            OpenStack service name (e.g. keystone). Mutually exclusive with
            service_id. One of service_name or service_id is required.
     required: false
   service_id:
     description:
        - |
            OpenStack service id. Mutually exclusive with service_name. One of
            service_name or service_id is required.
     required: false
   region:
     description:
        - OpenStack region to which endpoint will be added
     required: false
     default: None
   public_url:
     description:
        - Public endpoint URL
     required: true
   internal_url:
     description:
        - Internal endpoint URL
     required: false
     default: None
   admin_url:
     description:
        - Admin endpoint URL
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
requirements: ["shade"]
author: Davide Guerri
'''

EXAMPLES = '''
# Create a Glance endpoint in region aw1
- name: Create Glance endpoints
  os_keystone_endpoint: >
    service_name="glance"
    region="aw1"
    public_url="https://glance.aw1.bigcompany.com/"
    internal_url="http://glance-aw1.internal:9292/"
    admin_url="https://glance.aw1.bigcompany.com/"
    state=present
    cloud: dguerri

# Delete a Keystone endpoint in region aw2
- name: Delete Glance endpoints
  os_keystone_endpoint: >
    service_name="glance"
    region="aw2"
    public_url="https://glance.aw1.bigcompany.com/"
    internal_url="http://glance-aw1.internal:9292/"
    admin_url="https://glance.aw1.bigcompany.com/"
    state="absent"
    cloud: dguerri
'''


def main():
    argument_spec = openstack_full_argument_spec()
    argument_spec.update(dict(
        service_name=dict(),
        service_id=dict(),
        region=dict(required=False, default=None),
        public_url=dict(required=True),
        internal_url=dict(required=False, default=None),
        admin_url=dict(required=False, default=None),
        state=dict(default='present', choices=['present', 'absent']),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['service_name', 'service_id']],
        required_one_of=[['service_name', 'service_id']]
    )

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    service_name = module.params['service_name']
    service_id = module.params['service_id']
    region = module.params['region']
    public_url = module.params['public_url']
    internal_url = module.params['internal_url']
    admin_url = module.params['admin_url']
    state = module.params['state']

    check_mode = module.check_mode

    try:
        cloud = shade.operator_cloud(**module.params)

        # Determine service id
        if service_id is None:
            service = cloud.get_service(name_or_id=service_name)
            service_id = service.id

        endpoint_kwargs = dict(
            service_id=service_id,
            publicurl=public_url,
            internalurl=internal_url,
            adminurl=admin_url,
            region=region)

        endpoints = cloud.search_endpoints(filters=endpoint_kwargs)
        if endpoints:
            endpoint = endpoints[0]
        else:
            endpoint = None

        if state == "present":
            if endpoint is None:
                if module.check_mode:
                    module.exit_json(changed=True)

                new_endpoint = cloud.create_endpoint(
                    service_name_or_id=service_id, public_url=public_url,
                    internal_url=internal_url, admin_url=admin_url,
                    region=region)
                module.exit_json(changed=True,
                                 result='created',
                                 id=new_endpoint['id'])
            else:
                # Endpoint is already there
                module.exit_json(changed=False,
                                 result='success',
                                 id=endpoint['id'])
        elif state == "absent":
            if module.check_mode:
                module.exit_json(changed=endpoint is not None)

            if endpoint is not None:
                cloud.delete_endpoint(id=endpoint['id'])
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
