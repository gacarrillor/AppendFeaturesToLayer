import nose2

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import (get_test_file_copy_path,
                         get_qgis_gpkg_layer,
                         APPENDED_COUNT,
                         SKIPPED_COUNT,
                         UPDATED_FEATURE_COUNT,
                         UPDATED_ONLY_GEOMETRY_COUNT)

start_app()


class TestParameterErrors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\nINFO: Set up test_parameter_errors')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        cls.plugin = AppendFeaturesToLayerPlugin(get_iface)
        cls.plugin.initGui()

    def test_fields_no_on_duplicate(self):
        print('\nINFO: Validating fields with no on_duplicate option...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'SOURCE_LAYER': "{}|layername=source_table".format(gpkg),
                        'SOURCE_FIELD': 'name',
                        'TARGET_LAYER': "{}|layername=target_table".format(gpkg),
                        'TARGET_FIELD': 'name',
                        'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertIsNone(res['TARGET_LAYER'])  # The algorithm doesn't run, and doesn't give an output
        self.assertIsNone(res[APPENDED_COUNT])
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])
        self.assertIsNone(res[SKIPPED_COUNT])

        # Target layer remains untouched
        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.featureCount(), 0)

    def test_no_fields_but_on_duplicate(self):
        print('\nINFO: Validating no fields but with on_duplicate option...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'SOURCE_LAYER': "{}|layername=source_table".format(gpkg),
                        'SOURCE_FIELD': None,
                        'TARGET_LAYER': "{}|layername=target_table".format(gpkg),
                        'TARGET_FIELD': 'name',
                        'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertIsNone(res['TARGET_LAYER'])  # The algorithm doesn't run, and doesn't give an output
        self.assertIsNone(res[APPENDED_COUNT])
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])
        self.assertIsNone(res[SKIPPED_COUNT])

        # Target layer remains untouched
        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.featureCount(), 0)


        # Now the other way around
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': "{}|layername=source_table".format(gpkg),
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': "{}|layername=target_table".format(gpkg),
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertIsNone(res['TARGET_LAYER'])  # The algorithm doesn't run, and doesn't give an output
        self.assertIsNone(res[APPENDED_COUNT])
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])
        self.assertIsNone(res[SKIPPED_COUNT])

        # Target layer remains untouched
        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.featureCount(), 0)

    def test_read_only_target_layer(self):
        print('\nINFO: Validating read-only target layer...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')
        csv = get_test_file_copy_path('sample.csv')
        layer = QgsVectorLayer("file://{}?delimiter=;&xField=x&yField=y&crs=epsg:3116".format(csv), 'a', "delimitedtext")
        self.assertTrue(layer.isValid())

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'SOURCE_LAYER': "{}|layername=source_table".format(gpkg),
                        'SOURCE_FIELD': None,
                        'TARGET_LAYER': layer,
                        'TARGET_FIELD': None,
                        'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertIsNone(res['TARGET_LAYER'])  # The algorithm doesn't run, and doesn't give an output
        self.assertIsNone(res[APPENDED_COUNT])
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])
        self.assertIsNone(res[SKIPPED_COUNT])

        self.assertEqual(layer.featureCount(), 2)

    def test_dont_only_update_geometries_when_layer_is_not_spatial(self):
        print('\nINFO: Validating (only) geometries cannot be updated if target layer is non-spatial...')

        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        input_layer_path = "{}|layername={}".format(layer_path, 'source_simple_polygons')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'SOURCE_LAYER': input_layer,
                        'SOURCE_FIELD': 'name',
                        'TARGET_LAYER': output_layer,
                        'TARGET_FIELD': 'name',
                        'ACTION_ON_DUPLICATE': 3})  # Only update geometries

        self.assertIsNone(res['TARGET_LAYER'])  # The algorithm doesn't run, and doesn't give an output
        self.assertIsNone(res[APPENDED_COUNT])
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])
        self.assertIsNone(res[UPDATED_ONLY_GEOMETRY_COUNT])
        self.assertIsNone(res[SKIPPED_COUNT])

        self.assertEqual(output_layer.featureCount(), 0)

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_parameter_errors')
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()
