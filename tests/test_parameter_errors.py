import nose2

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import get_test_file_copy_path

start_app()

class TestParameterErrors(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_parameter_errors')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()

    def test_fields_no_on_duplicate(self):
        print('\nINFO: Validating fields with no on_duplicate option...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'INPUT': "{}|layername=source_table".format(gpkg),
                        'INPUT_FIELD': 'name',
                        'OUTPUT': "{}|layername=target_table".format(gpkg),
                        'OUTPUT_FIELD': 'name',
                        'ACTION_ON_DUPLICATE': None})

        self.assertIsNone(res['OUTPUT'])  # The algorithm doesn't run, and doesn't give an output

        # Target layer remains untouched
        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertEqual(layer.featureCount(), 0)

    def test_no_fields_but_on_duplicate(self):
        print('\nINFO: Validating no fields but with on_duplicate option...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'INPUT': "{}|layername=source_table".format(gpkg),
                        'INPUT_FIELD': None,
                        'OUTPUT': "{}|layername=target_table".format(gpkg),
                        'OUTPUT_FIELD': 'name',
                        'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertIsNone(res['OUTPUT'])  # The algorithm doesn't run, and doesn't give an output

        # Target layer remains untouched
        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertEqual(layer.featureCount(), 0)


        # Now the other way around
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': "{}|layername=source_table".format(gpkg),
                              'INPUT_FIELD': 'name',
                              'OUTPUT': "{}|layername=target_table".format(gpkg),
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertIsNone(res['OUTPUT'])  # The algorithm doesn't run, and doesn't give an output

        # Target layer remains untouched
        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertEqual(layer.featureCount(), 0)


    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_parameter_errors')
        self.plugin.unload()

if __name__ == '__main__':
    nose2.main()


