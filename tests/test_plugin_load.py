import nose2

from qgis.core import QgsApplication
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

start_app()

class TestPluginLoad(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_plugin_load')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()

    def test_plugin_load(self):
        print('INFO: Validating plugin load...')
        self.assertIsNotNone(self.plugin.provider)
        self.assertIn("ETL_LOAD", [provider.name() for provider in QgsApplication.processingRegistry().providers()])

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_plugin_load')
        self.plugin.unload()

if __name__ == '__main__':
    nose2.main()
