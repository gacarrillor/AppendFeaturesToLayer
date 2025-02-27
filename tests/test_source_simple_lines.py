from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

from tests.utils import (CommonTests,
                         get_qgis_gpkg_layer,
                         APPENDED_COUNT)

start_app()


class TestSimplePolySimpleLine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\nINFO: Set up simple_pol-simple_lin')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        cls.plugin = AppendFeaturesToLayerPlugin(get_iface)
        cls.plugin.initGui()
        cls.common = CommonTests()

    def test_copy_all(self):
        print('\nINFO: Validating simple_pol-simple_lin copy&paste all...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_lines')
        res = self.common._test_copy_all('source_simple_polygons', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)  # The second geometry is not simple and thus, is not copied

    def test_copy_selected(self):
        print('\nINFO: Validating simple_pol-simple_lin copy&paste selected...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_lines')
        res = self.common._test_copy_selected('source_simple_polygons', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 0)  # Selected id has a hole, cannot be copied
        self.assertEqual(res[APPENDED_COUNT], 0)

        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_lines')
        res = self.common._test_copy_selected('source_simple_polygons', output_layer, layer_path, select_id=2)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down simple_pol-simple_lin')
        cls.plugin.unload()
