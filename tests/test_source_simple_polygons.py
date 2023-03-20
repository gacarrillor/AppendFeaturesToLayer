import nose2

from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

from tests.utils import (CommonTests,
                         APPENDED_COUNT)

start_app()


class TestSimplePolySimplePoly(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up simple_pol-simple_pol')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()
        self.common = CommonTests()

    def test_copy_all(self):
        print('\nINFO: Validating simple_pol-simple_pol copy&paste all...')
        res = self.common._test_copy_all('source_simple_polygons', 'target_simple_polygons')
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res['APPENDED_COUNT'], 2)

    def test_copy_selected(self):
        print('\nINFO: Validating simple_pol-simple_pol copy&paste selected...')
        res = self.common._test_copy_selected('source_simple_polygons', 'target_simple_polygons')
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    def test_update(self):
        print('\nINFO: Validating simple_pol-simple_pol update...')
        self.common._test_update('source_simple_polygons', 'target_simple_polygons')

    def test_skip_all(self):
        print('\nINFO: Validating simple_pol-simple_pol skip (all) duplicate features...')
        self.common._test_skip_all('source_simple_polygons', 'target_simple_polygons')

    def test_skip_some(self):
        print('\nINFO: Validating simple_pol-simple_pol skip (some) duplicate features...')
        self.common._test_skip_some('source_simple_polygons', 'target_simple_polygons')

    def test_skip_none(self):
        print('\nINFO: Validating simple_pol-simple_pol skip (none) duplicate features...')
        self.common._test_skip_none('source_simple_polygons', 'target_simple_polygons')

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down simple_pol-simple_pol')
        self.plugin.unload()


class TestSimplePolySimpleLine(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up simple_pol-simple_lin')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()
        self.common = CommonTests()

    def test_copy_all(self):
        print('\nINFO: Validating simple_pol-simple_lin copy&paste all...')
        res = self.common._test_copy_all('source_simple_polygons', 'target_simple_lines')
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)

    def test_copy_selected(self):
        print('\nINFO: Validating simple_pol-simple_lin copy&paste selected...')
        res = self.common._test_copy_selected('source_simple_polygons', 'target_simple_lines')
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 0)  # Selected id has a hole, cannot be copied
        self.assertEqual(res[APPENDED_COUNT], 0)

        res = self.common._test_copy_selected('source_simple_polygons', 'target_simple_lines', 2)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down simple_pol-simple_lin')
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()
