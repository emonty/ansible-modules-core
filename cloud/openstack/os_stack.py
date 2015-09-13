#!/usr/bin/python
#
# Copyright (c) 2015, Taneli Leppa <rosmo@rosmo.fi>
# Based on os_keypair module
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

import json
import os
import time
try:
    import shade
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_stack
short_description: Manage Heat stacks on OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
description:
  - Manage Heat stacks on Openstack
options:
  name:
    description:
      - Name for the Heat stack
    required: true
  template_file:
    description:
      - File containing Heat Template (exclusive with template_url)
    required: false
    default: None
  template_url:
    description:
      - URL containing Heat Template (exclusive with template_file)
    required: false
    default: None
  files:
    description:
      - List of files to process alongside the template
    required: false
    default: None
  parameters:
    description:
      - Dictionary containing parameters for the Heat template.
    required: false
    default: None
  tags:
    description:
      - Tags for the Heat template.
    required: false
    default: None
  wait:
    description:
      - Wait for the stack creation to be complete.
    required: false
    default: True
  timeout:
    description:
      - Amount of time to wait for the stack creation to complete.
    required: false
    default: 120
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
  os_orchestration_stack:
     name: "teststack"
     template_file: '../templates/sample.yml.j2'
     state: present
     parameters:
       key_name: "my-key"
       flavor: "tiny"
       image: "my-image-name"
       availability_zone: "zone-1"
  connection: local
'''

RETURN = '''
info:
    description: Heat stack contents.
    returned: success
    type: dict
'''


def _json_helper(obj):
    import calendar, datetime

    if isinstance(obj, datetime.date):
        return obj.isoformat()

def main():
    argument_spec = openstack_full_argument_spec(
        login_tenant_id = dict(required=False),
        name = dict(required=True),
        template_file = dict(required=False, default=None),
        template_url = dict(required=False, default=None),
        files = dict(required=False, default=[], type='list'),
        parameters = dict(required=False, type='dict', default=None),
        tags = dict(required=False, type='list', default=None),
        wait = dict(required=False, default=True, type='bool'),
        timeout = dict(required=False, default=120, type='int'),
        state = dict(default='present', choices=['absent', 'present'])
    ))
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['template_file', 'template_url']
        ],
        required_if=[
            ('state', 'present', ['template']),
        ])
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        name = module.params.pop('name')
        parameters = module.params.pop('parameters')
        tags = ','.join(module.params.pop('tags'))
        template_file = module.params.pop('template_file')
        template_url = module.params.pop('template_url')
        files = module.params.pop('files')

        state = module.params.pop('state')

        cloud_params = dict(module.params)
        cloud = shade.openstack_cloud(**cloud_params)
        heat = cloud.heat_client

        found_stack = None
        stacks = heat.stacks.list()
        for stack in stacks:
            if stack.stack_name.lower() == module.params['name'].lower():
                found_stack = stack
                break

        if state == 'present':

            if not found_stack:
                tpl_files, template = cloud.get_template_contents(
                    template_file=template_file,
                    template_url=template_url,
                    files=files)

                _stack = heat.stacks.create(
                    stack_name=stack_name,
                    template=template,
                    files=tpl_files,
                    parameters=parameters,
                    tags=tags)
                found_stack = heat.stacks.get(_stack['stack']['id'])
                _stack_dict = found_stack.to_dict()
                if module.params['wait']:
                    expire = time.time() + module.params['timeout']
                    while time.time() < expire:
                        if _stack_dict['stack_status'] != 'CREATE_IN_PROGRESS':
                            break

                        time.sleep(2)
                        found_stack = heat.stacks.get(_stack['stack']['id'])
                        _stack_dict = found_stack.to_dict()
                module.exit_json(changed=True, info=_stack_dict)

            if found_stack:

                found_stack.get()
                _stack_dict = found_stack.to_dict()

                stack_template = heat.stacks.template(found_stack.identifier))
                changed = False
                if cmp(template, stack_template) != 0:
                    # TODO: This should check for more than just template
                    # change. Parameters, tags and files are all also things
                    # that could change
                    changed = True

                if changed:
                    _stack = heat.stacks.update(
                        found_stack.identifier,
                        stack_name=stack_name,
                        template=template,
                        files=tpl_files,
                        parameters=parameters,
                        tags=tags)
                    found_stack = heat.stacks.get(found_stack.identifier)
                    _stack_dict = found_stack.to_dict()
                    if module.params['wait']:
                        expire = time.time() + module.params['timeout']
                        while time.time() < expire:
                            if _stack_dict['stack_status'] != 'UPDATE_IN_PROGRESS':
                                break

                            time.sleep(2)
                            found_stack = heat.stacks.get(found_stack.identifier)
                            _stack_dict = found_stack.to_dict()

                    module.exit_json(changed=changed, info=_stack_dict)
                module.exit_json(changed=changed, info=_stack_dict)

        if state != 'present' and found_stack:
            heat.stacks.delete(found_stack.identifier)
            module.exit_json(changed=True)

        module.exit_json(changed=False)

    except Exception, e:
        module.fail_json(msg = "Heat error: %s" % e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
