import nose2

from qgis.core import QgsApplication
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

start_app()

class TestPluginLoad(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('INFO: setUp test_plugin_load')
        pass

    def test_plugin_load(self):
        print('INFO: Validating plugin load...')

        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        plugin = AppendFeaturesToLayerPlugin(get_iface)
        plugin.initGui()
        self.assertIsNotNone(plugin.provider)

        self.assertIn("ETL_LOAD", [provider.name() for provider in QgsApplication.processingRegistry().providers()])

    def tearDownClass():
        print('INFO: tearDown test_plugin_load')

if __name__ == '__main__':
    nose2.main()
