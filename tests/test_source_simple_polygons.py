import nose2

from qgis.PyQt.QtCore import QDate
from qgis.core import (QgsVectorLayerUtils,
                       QgsGeometry,
                       QgsVectorLayer)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import (CommonTests,
                         get_qgis_gpkg_layer,
                         APPENDED_COUNT,
                         SKIPPED_COUNT,
                         UPDATED_FEATURE_COUNT,
                         UPDATED_ONLY_GEOMETRY_COUNT)

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
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        res = self.common._test_copy_all('source_simple_polygons', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res['APPENDED_COUNT'], 2)

    def test_copy_selected(self):
        print('\nINFO: Validating simple_pol-simple_pol copy&paste selected...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        res = self.common._test_copy_selected('source_simple_polygons', output_layer, layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    def test_update(self):
        print('\nINFO: Validating simple_pol-simple_pol update...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        self.common._test_update('source_simple_polygons', output_layer, layer_path)

    def test_skip_all(self):
        print('\nINFO: Validating simple_pol-simple_pol skip (all) duplicate features...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        self.common._test_skip_all('source_simple_polygons', output_layer, layer_path)

    def test_skip_some(self):
        print('\nINFO: Validating simple_pol-simple_pol skip (some) duplicate features...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        self.common._test_skip_some('source_simple_polygons', output_layer, layer_path)

    def test_skip_none(self):
        print('\nINFO: Validating simple_pol-simple_pol skip (none) duplicate features...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        self.common._test_skip_none('source_simple_polygons', output_layer, layer_path)

    def test_only_update_geometry(self):
        print('\nINFO: Validating only update geometry when duplicates are found...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_simple_polygons')
        input_layer_path = "{}|layername={}".format(layer_path, 'source_simple_polygons')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')

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
                              'TARGET_FIELD': 'fid',
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
    def tearDownClass(self):
        print('INFO: Tear down simple_pol-simple_pol')
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()
