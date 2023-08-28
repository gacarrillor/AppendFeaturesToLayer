import nose2

from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

from tests.utils import (CommonTests,
                         get_qgis_pg_layer,
                         APPENDED_COUNT,
                         PG_BD_1,
                         prepare_pg_db_1,
                         drop_all_tables)

start_app()


class TestSimplePolySimplePoly(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\nINFO: Set up pg_simple_pol-simple_pol')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        cls.plugin = AppendFeaturesToLayerPlugin(get_iface)
        cls.plugin.initGui()
        cls.common = CommonTests()
        prepare_pg_db_1()

    def test_copy_all(self):
        print('\nINFO: Validating PG simple_pol-simple_pol copy&paste all...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons')
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self.common._test_copy_all('source_simple_polygons', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down pg_simple_pol-simple_pol')
        drop_all_tables()
        cls.plugin.unload()


if __name__ == '__main__':
    nose2.main()
