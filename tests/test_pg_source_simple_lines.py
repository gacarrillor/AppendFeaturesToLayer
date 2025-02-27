from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

from tests.utils import (CommonTests,
                         get_qgis_gpkg_layer,
                         prepare_pg_db_1,
                         get_qgis_pg_layer,
                         PG_BD_1,
                         drop_all_tables,
                         APPENDED_COUNT)

start_app()


class TestPGSimplePolySimpleLine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\nINFO: Set up simple_pol-simple_lin')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        cls.plugin = AppendFeaturesToLayerPlugin(get_iface)
        cls.plugin.initGui()
        cls.common = CommonTests()
        prepare_pg_db_1()

    def test_copy_all(self):
        print('\nINFO: Validating pg simple_pol-simple_lin copy&paste all...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_lines', 'geom', truncate=True)
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self.common._test_copy_all('source_simple_polygons', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)  # The second geometry is not simple and thus, is not copied

    def test_copy_selected(self):
        print('\nINFO: Validating pg simple_pol-simple_lin copy&paste selected...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_lines', 'geom', truncate=True)
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self.common._test_copy_selected('source_simple_polygons', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 0)  # Selected id has a hole, cannot be copied
        self.assertEqual(res[APPENDED_COUNT], 0)

        res = self.common._test_copy_selected('source_simple_polygons', pg_layer, select_id=2)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down pg simple_pol-simple_lin')
        drop_all_tables()
        cls.plugin.unload()
