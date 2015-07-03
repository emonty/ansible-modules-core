#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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
module: os_router_interface
short_description: Attach/Dettach a subnet's interface to a router
extends_documentation_fragment: openstack
version_added: "1.10"
description:
   - Attach/Dettach a subnet interface to a router, to provide a gateway for the subnet.
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   router_name:
     description:
        - Name of the router to which the subnet's interface should be attached.
     required: true
     default: None
   subnet_name:
     description:
        - Name of the subnet to whose interface should be attached to the router.
     required: true
     default: None
requirements: ["shade"]
'''

EXAMPLES = '''
# Attach subnet t1subnet to the external router external_route
- os_router_interface: state=present username=admin
                       password=admin
                       project_name=admin
                       router_name=external_route
                       subnet_name=t1subnet
'''


def _get_router_id(module, neutron):
    kwargs = {
        'name': module.params['router_name'],
    }
    try:
        routers = neutron.list_routers(**kwargs)
    except Exception, e:
        module.fail_json(msg = "Error in getting the router list: %s " % e.message)
    if not routers['routers']:
        return None
    return routers['routers'][0]['id']


def _get_subnet_id(module, neutron):
    subnet_id = None
    kwargs = {
            'name': module.params['subnet_name'],
    }
    try:
        subnets = neutron.list_subnets(**kwargs)
    except Exception, e:
        module.fail_json( msg = " Error in getting the subnet list:%s " % e.message)
    if not subnets['subnets']:
        return None
    return subnets['subnets'][0]['id']

def _get_port_id(neutron, module, router_id, subnet_id):
    kwargs = {
            'device_id': router_id,
    }
    try:
        ports = neutron.list_ports(**kwargs)
    except Exception, e:
        module.fail_json( msg = "Error in listing ports: %s" % e.message)
    if not ports['ports']:
        return None
    for port in  ports['ports']:
        for subnet in port['fixed_ips']:
            if subnet['subnet_id'] == subnet_id:
                return port['id']
    return None

def _add_interface_router(neutron, module, router_id, subnet_id):
    kwargs = {
        'subnet_id': subnet_id
    }
    try:
        neutron.add_interface_router(router_id, kwargs)
    except Exception, e:
        module.fail_json(msg = "Error in adding interface to router: %s" % e.message)
    return True

def  _remove_interface_router(neutron, module, router_id, subnet_id):
    kwargs = {
        'subnet_id': subnet_id
    }
    try:
        neutron.remove_interface_router(router_id, kwargs)
    except Exception, e:
        module.fail_json(msg="Error in removing interface from router: %s" % e.message)
    return True

def main():
    argument_spec = openstack_full_argument_spec(
        router_name                     = dict(required=True),
        subnet_name                     = dict(required=True),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        neutron = cloud.neutron_client

        router_id = _get_router_id(module, neutron)
        if not router_id:
            module.fail_json(msg="failed to get the router id, please check the router name")

        subnet_id = _get_subnet_id(module, neutron)
        if not subnet_id:
            module.fail_json(msg="failed to get the subnet id, please check the subnet name")

        if module.params['state'] == 'present':
            port_id = _get_port_id(neutron, module, router_id, subnet_id)
            if not port_id:
                _add_interface_router(neutron, module, router_id, subnet_id)
                module.exit_json(changed=True, result="created", id=port_id)
            module.exit_json(changed=False, result="success", id=port_id)

        if module.params['state'] == 'absent':
            port_id = _get_port_id(neutron, module, router_id, subnet_id)
            if not port_id:
                module.exit_json(changed = False, result = "Success")
            _remove_interface_router(neutron, module, router_id, subnet_id)
            module.exit_json(changed=True, result="Deleted")
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

