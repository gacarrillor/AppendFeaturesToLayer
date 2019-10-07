import nose2

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import CommonTests

start_app()

class TestTableTable(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_table_table')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()
        self.common = CommonTests()

    def test_copy_all(self):
        print('\nINFO: Validating table-table copy&paste all...')
        layer = self.common._test_copy_all('source_table', 'target_table')
        self.assertEqual(layer.featureCount(), 2)

    def test_copy_selected(self):
        print('\nINFO: Validating table-table copy&paste selected...')
        layer = self.common._test_copy_selected('source_table', 'target_table')
        self.assertEqual(layer.featureCount(), 1)

    def test_update(self):
        print('\nINFO: Validating table-table update...')
        self.common._test_update('source_table', 'target_table')

    def test_skip_all(self):
        print('\nINFO: Validating table-table skip (all) duplicate features...')
        self.common._test_skip_all('source_table', 'target_table')

    def test_skip_some(self):
        print('\nINFO: Validating table-table skip (some) duplicate features...')
        self.common._test_skip_some('source_table', 'target_table')

    def test_skip_none(self):
        print('\nINFO: Validating table-table skip (none) duplicate features...')
        self.common._test_skip_none('source_table', 'target_table')

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_table_table')
        self.plugin.unload()

if __name__ == '__main__':
    nose2.main()


