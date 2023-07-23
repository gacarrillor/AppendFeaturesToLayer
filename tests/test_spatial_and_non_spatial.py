import nose2

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature,
                       QgsGeometry)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import (APPENDED_COUNT,
                         SKIPPED_COUNT,
                         UPDATED_COUNT, CommonTests)

start_app()


class TestSpatialAndNonSpatialUpdates(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_parameter_errors')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()
        self.common = CommonTests()

    def test_update_spatial_features_from_non_spatial_layer(self):
        print('\nINFO: Validating geometries are not updated if source layer is non-spatial...')

        res = self.common._test_copy_selected('source_multi_polygons', 'target_multi_polygons')
        layer = res['TARGET_LAYER']
        original_geoms = [f.geometry().asWkt() for f in layer.getFeatures()]

        output_path = layer.source().split('|')[0]
        input_layer_path = "{}|layername={}".format(output_path, 'source_table')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'SOURCE_LAYER': input_layer,
                        'SOURCE_FIELD': 'name',
                        'TARGET_LAYER': layer,
                        'TARGET_FIELD': 'name',
                        'ACTION_ON_DUPLICATE': 2})  # Update

        #self.assertEqual(layer.featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertEqual(res[UPDATED_COUNT], 1)
        self.assertIsNone(res[SKIPPED_COUNT])

        # Geometry in target layer is not NULL and remained untouched
        updated_geoms = [f.geometry().asWkt() for f in layer.getFeatures()]
        for g in original_geoms:
            self.assertIn(g, updated_geoms)

        # Check that a NULL geometry (QgsGeometry()) has only been the result of the APPEND (1 feature),
        # while the other 2 features have still a non-NULL geometry
        self.assertEqual(updated_geoms.count(QgsGeometry().asWkt()), res[APPENDED_COUNT])

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_parameter_errors')
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()