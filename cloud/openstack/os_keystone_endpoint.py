#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Author: Davide Guerri <davide.guerri@hp.com>
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
module: os_keystone_endpoint
version_added: "2.0"
short_description: Manage OpenStack Identity endpoints
extends_documentation_fragment: openstack
description:
   - Manage endpoints from OpenStack.
options:
   service:
     description:
        - OpenStack service name or id (e.g. compute).
     required: true
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
    service="image"
    region="aw1"
    public_url="https://glance.aw1.bigcompany.com/"
    internal_url="http://glance-aw1.internal:9292/"
    admin_url="https://glance.aw1.bigcompany.com/"
    state=present
    cloud: dguerri

# Delete a Keystone endpoint in region aw2
- name: Delete Glance endpoints
  os_keystone_endpoint: >
    service="image"
    region="aw2"
    public_url="https://glance.aw1.bigcompany.com/"
    internal_url="http://glance-aw1.internal:9292/"
    admin_url="https://glance.aw1.bigcompany.com/"
    state="absent"
    cloud: dguerri
'''


def main():
    argument_spec = openstack_full_argument_spec(
        service=dict(required=True),
        region=dict(required=False, default=None),
        public_url=dict(required=True),
        internal_url=dict(required=False, default=None),
        admin_url=dict(required=False, default=None),
        state=dict(default='present', choices=['present', 'absent']),
    )
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
        service = cloud.get_service(name_or_id=service)
        if not service:
            module.fail_json(msg="Could not find service %s" % service)


        # TODO this needs to be replaced with new v2/v3 aware shade code
        endpoint_kwargs = dict(
            service_id=service.id,
            public_url=public_url,
            internal_url=internal_url,
            admin_url=admin_url,
            region=region)

        # TODO this needs to be replaced with new v2/v3 aware shade code
        endpoints = cloud.search_endpoints(filters=endpoint_kwargs)
        if endpoints:
            endpoint = endpoints[0]
        else:
            endpoint = None

        if state == "present":
            if endpoint is None:
                if module.check_mode:
                    module.exit_json(changed=True)

                del endpoint_kwargs['service_id']
                endpoint_kwargs['service_name_or_id'] = service_id
                new_endpoint = cloud.create_endpoint(**endpoint_kwargs)
                module.exit_json(changed=True, endpoint=new_endpoint)
            else:
                # Endpoint is already there
                module.exit_json(changed=False, endpoint=endpoint)
        elif state == "absent":
            if module.check_mode:
                module.exit_json(changed=endpoint is not None)

            if endpoint is not None:
                cloud.delete_endpoint(id=endpoint['id'])
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

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
