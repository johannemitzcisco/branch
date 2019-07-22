# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service

class BranchService(Service):
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        for device in service.device:
            if device.pnp_id is not None:
                self.log.info('Registering Device ({}) with PnP (ID: {})'.format(device.nso_name, \
                    device.pnp_id))
                vars = ncs.template.Variables()
                template = ncs.template.Template(device)
                template.apply('service-pnp-device', vars)

            if (root.pnp_state.device.exists(device.pnp_id) \
                and root.pnp_state.device[device.pnp_id].synced \
                and root.devices.device.exists(device.nso_name)) \
               or (root.devices.device.exists(device.nso_name) \
                   and device.pnp_id is None):
                for rolename in device.role:
                    self.log.info("Applying role ({})".format(rolename))                        
                    role = root.device_role[rolename]
                    for templatename in role.template:  
                        self.log.info('Apply Template ({}) to device ({})'.format(templatename, \
                            device.nso_name))
                        input = root.devices.device[device.nso_name].apply_template.get_input()
                        input.template_name = templatename
                        output = root.devices.device[device.nso_name].apply_template(input)

            else:
                kick_monitor_node = ("/pnp-state/device[serial='{}']/synced").format(device.pnp_id)
                self.log.info('Creating Kicker Monitor on: ', kick_monitor_node)
                kicker = root.kickers.data_kicker.create('branch-device-{}'.format(device.name))
                kicker.monitor = kick_monitor_node
                kicker.kick_node = ("/branch[name='{}']").format(service.name)
                kicker.action_name = 'reactive-re-deploy'

class Main(ncs.application.Application):
    def setup(self):
        self.log.info('Main RUNNING')
        self.register_service('branch-servicepoint', BranchService)

    def teardown(self):
        self.log.info('Main FINISHED')
