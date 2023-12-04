import nose2

from qgis.PyQt.QtCore import QDate
from qgis.core import (QgsVectorLayerUtils,
                       QgsGeometry,
                       QgsVectorLayer)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface
import processing

from tests.utils import (CommonTests,
                         get_qgis_pg_layer,
                         APPENDED_COUNT,
                         SKIPPED_COUNT,
                         UPDATED_FEATURE_COUNT,
                         UPDATED_ONLY_GEOMETRY_COUNT,
                         PG_BD_1,
                         prepare_pg_db_1,
                         drop_all_tables,
                         get_qgis_gpkg_layer)

start_app()


class TestPGSimplePolySimplePoly(unittest.TestCase):

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

    def test_copy_selected(self):
        print('\nINFO: Validating pg simple_pol-simple_pol copy&paste selected...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons', truncate=True)
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self.common._test_copy_selected('source_simple_polygons', pg_layer)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    def test_update(self):
        print('\nINFO: Validating pg simple_pol-simple_pol update...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons', truncate=True)
        self.common._test_update('source_simple_polygons', pg_layer)

    def test_skip_all(self):
        print('\nINFO: Validating pg simple_pol-simple_pol skip (all) duplicate features...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons', truncate=True)
        self.common._test_skip_all('source_simple_polygons', pg_layer)

    def test_skip_some(self):
        print('\nINFO: Validating pg simple_pol-simple_pol skip (some) duplicate features...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons', truncate=True)
        self.common._test_skip_some('source_simple_polygons', pg_layer)

    def test_skip_none(self):
        print('\nINFO: Validating pg simple_pol-simple_pol skip (none) duplicate features...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons', truncate=True)
        self.common._test_skip_none('source_simple_polygons', pg_layer)

    def test_only_update_geometry(self):
        print('\nINFO: Validating pg only update geometry when duplicates are found...')
        output_layer = get_qgis_pg_layer(PG_BD_1, 'target_simple_polygons', 'geom', truncate=True)
        input_layer, layer_path = get_qgis_gpkg_layer('source_simple_polygons')

        # Let's create a feature that will be updated later
        geom = QgsGeometry()
        attrs = {0: 2,
                 1: 'DEF',
                 2: 20.0,
                 3: QDate(84,2,19),
                 4: '0.1234'}
        new_feature = QgsVectorLayerUtils().createFeature(output_layer, geom, attrs)
        output_layer.dataProvider().addFeatures([new_feature])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'fid',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'id',
                              'ACTION_ON_DUPLICATE': 3})  # Only update geometries

        self.assertIsNotNone(res['TARGET_LAYER'])
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])
        self.assertEqual(res[UPDATED_ONLY_GEOMETRY_COUNT], 1)
        self.assertIsNone(res[SKIPPED_COUNT])

        self.assertEqual(output_layer.featureCount(), 2)

        # We should now have an updated geometry, not QgsGeometry() anymore
        new_wkt = 'Polygon ((1001318.1368170625064522 1013949.56026844482403249, 1001353.78617076261434704 1013933.86301946395542473, 1001321.19123999250587076 1013859.39660056948196143, 1001285.90720375021919608 1013876.74864967621397227, 1001318.1368170625064522 1013949.56026844482403249))'
        feature = output_layer.getFeature(2)
        self.assertEqual(feature.geometry().asWkt(), new_wkt)

        # Attrs should be intact
        old_attrs = [2, 'DEF', 20.0, QDate(84, 2, 19), '0.1234']
        self.assertEqual(feature.attributes(), old_attrs)

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down pg_simple_pol-simple_pol')
        drop_all_tables()
        cls.plugin.unload()


if __name__ == '__main__':
    nose2.main()
