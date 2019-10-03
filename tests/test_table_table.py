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

class TestTableTable(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_table_table')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()

    def test_copy_all(self):
        print('\nINFO: Validating table-table copy&paste all...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                       {'INPUT': "{}|layername=source_table".format(gpkg),
                        'INPUT_FIELD': None,
                        'OUTPUT': "{}|layername=target_table".format(gpkg),
                        'OUTPUT_FIELD': None,
                        'ACTION_ON_DUPLICATE': None})

        layer = QgsVectorLayer("{}|layername=target_table".format(gpkg), 'a', 'ogr')
        self.assertTrue(layer.isValid())
        self.assertEqual(layer.featureCount(), 2)

    def test_copy_selected(self):
        print('\nINFO: Validating table-table copy&paste selected...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername=source_table".format(gpkg)
        output_layer_path = "{}|layername=target_table".format(gpkg)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer(output_layer_path, 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        input_layer.select(1)  # fid=1

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': QgsProcessingFeatureSourceDefinition(input_layer_path, True),
                              'INPUT_FIELD': None,
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        self.assertEqual(res['OUTPUT'].featureCount(), 1)

    def test_update(self):
        print('\nINFO: Validating table-table update...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername=source_table".format(gpkg)
        output_layer_path = "{}|layername=target_table".format(gpkg)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer(output_layer_path, 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': None,
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        self.assertEqual(res['OUTPUT'].featureCount(), 2)

        input_layer.dataProvider().changeAttributeValues({1: {3: 30}})  # real_value --> 30
        new_feature = QgsFeature()
        new_feature.setAttributes([5, 'ABC', 1, 2.0])
        input_layer.dataProvider().addFeatures([new_feature])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': 'name',
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 2})  # Update

        self.assertEqual(res['OUTPUT'].featureCount(), 3)

        feature = next(output_layer.getFeatures('"name"=\'abc\''))
        self.assertEqual(feature['real_value'], 30)

        feature = next(output_layer.getFeatures('"name"=\'ABC\''))
        self.assertEqual(feature['real_value'], 2.0)

    def test_skip_all(self):
        print('\nINFO: Validating table-table skip (all) duplicate features...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername=source_table".format(gpkg)
        output_layer_path = "{}|layername=target_table".format(gpkg)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer(output_layer_path, 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': None,
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        self.assertEqual(res['OUTPUT'].featureCount(), 2)

        input_layer.dataProvider().changeAttributeValues({1: {3: 30}})  # real_value --> 30
        input_layer.dataProvider().changeAttributeValues({2: {3: 50}})  # real_value --> 50

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': 'name',
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(res['OUTPUT'].featureCount(), 2)

        feature = next(output_layer.getFeatures('"name"=\'abc\''))
        self.assertEqual(feature['real_value'], 3.1416)

        feature = next(output_layer.getFeatures('"name"=\'def\''))
        self.assertEqual(feature['real_value'], 1.41)

    def test_skip_some(self):
        print('\nINFO: Validating table-table skip (some) duplicate features...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername=source_table".format(gpkg)
        output_layer_path = "{}|layername=target_table".format(gpkg)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer(output_layer_path, 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': None,
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        self.assertEqual(res['OUTPUT'].featureCount(), 2)

        input_layer.dataProvider().changeAttributeValues({1: {3: 30}})  # real_value --> 30
        new_feature = QgsFeature()
        new_feature.setAttributes([5, 'ABC', 1, 2.0])
        input_layer.dataProvider().addFeatures([new_feature])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': 'name',
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(res['OUTPUT'].featureCount(), 3)

        feature = next(output_layer.getFeatures('"name"=\'abc\''))
        self.assertEqual(feature['real_value'], 3.1416)

        feature = next(output_layer.getFeatures('"name"=\'ABC\''))
        self.assertEqual(feature['real_value'], 2.0)

    def test_skip_none(self):
        print('\nINFO: Validating table-table skip (none) duplicate features...')

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername=source_table".format(gpkg)
        output_layer_path = "{}|layername=target_table".format(gpkg)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer(output_layer_path, 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': None,
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        self.assertEqual(res['OUTPUT'].featureCount(), 2)

        input_layer.dataProvider().changeAttributeValues({1: {1: 'abcd'}})  # text_value --> abcd
        input_layer.dataProvider().changeAttributeValues({2: {1: 'defg'}})  # text_value --> defg

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': input_layer,
                              'INPUT_FIELD': 'name',
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(res['OUTPUT'].featureCount(), 4)

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_table_table')
        self.plugin.unload()

if __name__ == '__main__':
    nose2.main()


