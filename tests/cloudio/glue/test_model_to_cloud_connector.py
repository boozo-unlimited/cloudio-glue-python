import unittest

from cloudio.endpoint.runtime import CloudioRuntimeNode


class FakeCloudioEndpoint(object):

    def add_node(self, node, object):
        pass

    def find_object(self, name):
        return None

    def add_object(self, name, object):
        return None


class Model2CloudioConnTestCase(unittest.TestCase):
    MINIMAL_ATTRIBUTE_MAPPING = {'name': {'id': 'test', 'type': 'embedded',
                                          'objectName': 'forest', 'attributeName': 'priority',
                                          'attributeType': int, 'constraints': ('read',)}, }

    OLD_ATTRIBUTE_MAPPING = {'name': {'id': 'test', 'type': 'embedded',
                                      'objectName': 'forest', 'attributeName': 'priority',
                                      'attributeType': int, 'constraints': ('read',)}, }

    DEFAULT_ATTRIBUTE_MAPPING = {'name': {'id': 'test', 'type': 'embedded',
                                          'topic': 'forest.priority',
                                          'attributeType': int, 'constraints': ('read',)}, }

    WRITE_ATTRIBUTE_MAPPING = {'enable': {'topic': 'enable.enable', 'attributeType': bool,
                                          'constraints': ('write',)}}

    def test_object_creation_failed_01(self):
        from cloudio.glue import Model2CloudConnector
        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        cc.set_cloudio_buddy(node)

        with self.assertRaises(KeyError):
            # 'constraint' key missing in dict
            cc.set_attribute_mapping({'name': {'id': 'test', 'type': 'embedded'}, })

    def test_object_creation_failed_02(self):
        from cloudio.glue import Model2CloudConnector
        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        # 'constraint' key missing in dict
        cc.set_attribute_mapping({'name': {'id': 'test', 'type': 'embedded'}, })

        with self.assertRaises(KeyError):
            cc.set_cloudio_buddy(node)

    def test_object_creation_success_01(self):
        from cloudio.glue import Model2CloudConnector
        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        # 'constraint' key missing in dict
        cc.set_attribute_mapping(self.MINIMAL_ATTRIBUTE_MAPPING)

        cc.set_cloudio_buddy(node)

    def test_create_cloud_io_node_01(self):
        from cloudio.glue.model_to_cloud_connector import Model2CloudConnector

        ep = FakeCloudioEndpoint()
        cc = Model2CloudConnector()

        cc.create_cloud_io_node(ep)

    def test_create_cloud_io_node_02(self):
        from cloudio.glue.model_to_cloud_connector import Model2CloudConnector

        ep = FakeCloudioEndpoint()
        cc = Model2CloudConnector()

        cc.set_attribute_mapping(self.DEFAULT_ATTRIBUTE_MAPPING)

        cc.create_cloud_io_node(ep)

    def test_create_cloud_io_node_03(self):
        from cloudio.glue.model_to_cloud_connector import Model2CloudConnector

        ep = FakeCloudioEndpoint()
        cc = Model2CloudConnector()

        cc.set_attribute_mapping(self.WRITE_ATTRIBUTE_MAPPING)

        cc.create_cloud_io_node(ep)

    def test_create_cloudio_object(self):
        from cloudio.glue.model_to_cloud_connector import Model2CloudConnector

        ep = FakeCloudioEndpoint()
        cc = Model2CloudConnector()

        cc.set_attribute_mapping(self.MINIMAL_ATTRIBUTE_MAPPING)

        node = cc.create_cloud_io_node(ep)
        self.assertIsNotNone(node)

        cc.create_cloudio_object(node, location_stack=['ep', 'test-endpoint', 'node', 'test-node', 'objects'])

    def test_setup_attribute_mapping(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        cc.set_cloudio_buddy(node)
        with self.assertRaises(KeyError):
            # 'attributeName' key missing in attribute_mapping
            cc.set_attribute_mapping({'enable': {'attributeType': bool, 'constraints': ('write',)}})

        cc.set_attribute_mapping({'enable': {'topic': 'test.it', 'attributeType': bool, 'constraints': ('write',)}})

        # Add the missing attribute 'test.it'
        obj = node.add_object('test', CloudioRuntimeObject)
        obj.add_attribute('it', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        cc.set_attribute_mapping({'enable': {'topic': 'test.it', 'attributeType': bool, 'constraints': ('write',)}})

        cc.set_attribute_mapping(
            {'enable': {'objectName': 'test', 'attributeName': 'unknown',
                        'attributeType': bool, 'constraints': ('write',)}})

    def test_location_stack_from_topic(self):
        from cloudio.glue import Model2CloudConnector

        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        cc.set_cloudio_buddy(node)
        cc.set_attribute_mapping(self.DEFAULT_ATTRIBUTE_MAPPING)

        # Check that node name gets removed
        location_stack = cc._location_stack_from_topic('cloudio-node.object.attribute')
        self.assertListEqual(location_stack, ['attribute', 'attributes', 'object', 'objects'])

    def test_attribute_has_changed_old_mapping_style(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        cc.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        cc.set_attribute_mapping({'power': {'objectName': 'property', 'attributeName': 'power',
                                            'attributeType': bool,
                                            'constraints': ('write',)}})

        result = cc.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertFalse(result)

    def test_attribute_has_changed_new_mapping_style(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('cloudio-node')

        cc.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        cc.set_attribute_mapping({'power': {'topic': 'property.power',
                                            'attributeType': bool,
                                            'constraints': ('write',)}})

        result = cc.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertFalse(result)

        # Try to pass a cloudio attribute not present in tree
        orphaned_attribute = CloudioAttribute()
        result = cc.attribute_has_changed(orphaned_attribute, from_cloud=True)
        self.assertFalse(result)

    def test_update_cloudio_attribute_new_mapping_style(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        cc.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        cc.set_attribute_mapping({'power': {'topic': 'property.power',
                                            'attributeType': bool,
                                            'constraints': ('write',)}})

        cc._update_cloudio_attribute('power', True)

    def test_update_cloudio_attribute_old_mapping_style(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        cc = Model2CloudConnector()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        cc.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)

        cc.set_attribute_mapping({'power': {'objectName': 'property', 'attributeName': 'power',
                                            'attributeType': bool,
                                            'constraints': ('write',)}})
        cc._update_cloudio_attribute('power', True)

    def test_update_cloudio_attribute_value_converter(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class DeviceModel(Model2CloudConnector):
            def __init__(self):
                super(DeviceModel, self).__init__()

            def value_converter(self, value):
                return value * 10

        model = DeviceModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        model.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)

        model.set_attribute_mapping({'power': {'objectName': 'property', 'attributeName': 'power',
                                               'attributeType': bool,
                                               'toCloudioValueConverter': model.value_converter,
                                               'constraints': ('write',)}})
        model._update_cloudio_attribute('power', True)

    def test_update_cloudio_attribute_not_present(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class DeviceModel(Model2CloudConnector):
            def __init__(self):
                super(DeviceModel, self).__init__()

            def value_converter(self, value):
                return value * 10

        model = DeviceModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        model.set_cloudio_buddy(node)

        # Add attribute 'property.other'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('other', bool, CloudioAttributeConstraint('static'), CloudioAttribute)

        model.set_attribute_mapping({'power': {'objectName': 'property', 'attributeName': 'power',
                                               'attributeType': bool,
                                               'constraints': ('write',)}})
        model._update_cloudio_attribute('power', True)

        # What happens if an attribute is not present?
        model._update_cloudio_attribute('not_present', True)

    def test_update_cloudio_attributes(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class DeviceModel(Model2CloudConnector):
            def __init__(self):
                super(DeviceModel, self).__init__()
                self.running = False

        model = DeviceModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        model.set_cloudio_buddy(node)

        # Add attribute 'property.running'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('running', bool, CloudioAttributeConstraint('static'), CloudioAttribute)

        model._update_cloudio_attributes()

        model.set_attribute_mapping({'running': {'objectName': 'property', 'attributeName': 'running',
                                                 'attributeType': bool,
                                                 'constraints': ('read',)},
                                     'missing': {'objectName': 'property', 'attributeName': 'running',
                                                 'attributeType': bool,
                                                 'constraints': ('read',)}
                                     })

        model._update_cloudio_attributes()

        model._force_update_of_cloudio_attributes()


class TestModel2CloudioConnectorCallbacks(unittest.TestCase):

    def test_attribute_has_changed_callbacks_01_success(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            def on_attribute_set_from_cloud(self, attribute_name, cloudio_attr):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        result = heater.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertTrue(result)
        self.assertTrue(heater.callback_called)

    def test_attribute_has_changed_callbacks_01_failed(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            # Bad parameter list
            def on_attribute_set_from_cloud(self):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        with self.assertLogs() as log:
            result = heater.attribute_has_changed(power_attribute, from_cloud=True)
            self.assertEqual(log.output[0],
                             'ERROR:cloudio.glue.model_to_cloud_connector:Exception : on_attribute_set_from_cloud() '
                             'takes 1 positional argument but 3 were given')

        self.assertFalse(result)
        self.assertFalse(heater.callback_called)

    def test_attribute_has_changed_callbacks_02_success(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            def on_power_set_from_cloud(self, value):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        result = heater.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertTrue(result)
        self.assertTrue(heater.callback_called)

    def test_attribute_has_changed_callbacks_02_failed(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            # Bad parameter list
            def on_power_set_from_cloud(self, value, bad_parameter):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        with self.assertLogs() as log:
            result = heater.attribute_has_changed(power_attribute, from_cloud=True)
            self.assertEqual(log.output[0],
                             "ERROR:cloudio.glue.model_to_cloud_connector:Exception : on_power_set_from_cloud() "
                             "missing 1 required positional argument: 'bad_parameter'")

        self.assertFalse(result)
        self.assertFalse(heater.callback_called)

    def test_attribute_has_changed_callbacks_03_success(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            def power(self, value):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        result = heater.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertTrue(result)
        self.assertTrue(heater.callback_called)

    def test_attribute_has_changed_callbacks_03_failed(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            # Bad parameter list
            def power(self, value, bad_parameter):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        with self.assertLogs() as log:
            result = heater.attribute_has_changed(power_attribute, from_cloud=True)
            self.assertEqual(log.output[0],
                             'ERROR:cloudio.glue.model_to_cloud_connector:Exception : power() missing 1 '
                             'required positional argument: \'bad_parameter\'')

        self.assertFalse(result)
        self.assertFalse(heater.callback_called)

    def test_attribute_has_changed_callbacks_04_success(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            def set_power(self, value):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        result = heater.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertTrue(result)
        self.assertTrue(heater.callback_called)

    def test_attribute_has_changed_callbacks_04_failed(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.callback_called = False

            # Bad parameter list
            def set_power(self, value, bad_parameter):
                self.callback_called = True

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        with self.assertLogs() as log:
            result = heater.attribute_has_changed(power_attribute, from_cloud=True)
            self.assertEqual(log.output[0],
                             'ERROR:cloudio.glue.model_to_cloud_connector:Exception : set_power() missing 1 '
                             'required positional argument: \'bad_parameter\'')

        self.assertFalse(result)
        self.assertFalse(heater.callback_called)

    def test_attribute_has_changed_callbacks_05_success(self):
        from cloudio.glue import Model2CloudConnector
        from cloudio.endpoint.runtime import CloudioRuntimeObject
        from cloudio.endpoint.attribute import CloudioAttribute, CloudioAttributeConstraint

        class HeaterModel(Model2CloudConnector):
            def __init__(self):
                super(HeaterModel, self).__init__()
                self.power = False

        heater = HeaterModel()
        node = CloudioRuntimeNode()
        node.set_name('heater')

        heater.set_cloudio_buddy(node)

        # Add attribute 'property.power'
        obj = node.add_object('property', CloudioRuntimeObject)
        power_attribute = obj.add_attribute('power', bool, CloudioAttributeConstraint('static'), CloudioAttribute)
        heater.set_attribute_mapping({'power': {'topic': 'property.power',
                                                'attributeType': bool,
                                                'constraints': ('write',)}})

        power_attribute.set_value(True)
        result = heater.attribute_has_changed(power_attribute, from_cloud=True)
        self.assertTrue(result)
        self.assertTrue(heater.power)


if __name__ == '__main__':
    unittest.main()
