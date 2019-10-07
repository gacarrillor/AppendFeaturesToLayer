import os
import tempfile
import unittest
from shutil import copyfile

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProject,
                       QgsProcessingFeatureSourceDefinition,
                       QgsFeature)
from qgis.analysis import QgsNativeAlgorithms
import qgis.utils

import processing

from qgis.testing.mocked import get_iface

# def get_iface():
#     global iface
#
#     def rewrite_method():
#         return "I'm rewritten"
#     iface.rewrite_method = rewrite_method
#     return iface

def get_test_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, "resources", path)

def get_test_file_copy_path(path):
    src_path = get_test_path(path)
    dst_path = os.path.split(src_path)
    dst_path = os.path.join(dst_path[0], next(tempfile._get_candidate_names()) + dst_path[1])
    print("-->", src_path, dst_path)
    copyfile(src_path, dst_path)
    return dst_path

def import_processing():
    global iface
    plugin_found = "processing" in qgis.utils.plugins
    if not plugin_found:
        processing_plugin = processing.classFactory(iface)
        qgis.utils.plugins["processing"] = processing_plugin
        qgis.utils.active_plugins.append("processing")

        from processing.core.Processing import Processing
        Processing.initialize()
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())


class CommonTests(unittest.TestCase):
    """ Utility functions """

    def _test_copy_all(self, input_layer_name, output_layer_name):
        print("### ", input_layer_name, output_layer_name)
        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': "{}|layername={}".format(gpkg, input_layer_name),
                              'INPUT_FIELD': None,
                              'OUTPUT': "{}|layername={}".format(gpkg, output_layer_name),
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        layer = QgsVectorLayer("{}|layername={}".format(gpkg, output_layer_name), 'a', 'ogr')
        self.assertTrue(layer.isValid())
        #self.assertEqual(layer.featureCount(), 2)
        return layer

    def _test_copy_selected(self, input_layer_name, output_layer_name, select_id=1):
        print("### ", input_layer_name, output_layer_name)
        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(gpkg, input_layer_name)
        output_layer_path = "{}|layername={}".format(gpkg, output_layer_name)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer(output_layer_path, 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        input_layer.select(select_id)  # fid=1

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'INPUT': QgsProcessingFeatureSourceDefinition(input_layer_path, True),
                              'INPUT_FIELD': None,
                              'OUTPUT': output_layer,
                              'OUTPUT_FIELD': None,
                              'ACTION_ON_DUPLICATE': None})

        return res['OUTPUT']

    def _test_update(self, input_layer_name, output_layer_name):
        print("### ", input_layer_name, output_layer_name)
        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(gpkg, input_layer_name)
        output_layer_path = "{}|layername={}".format(gpkg, output_layer_name)
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

    def _test_skip_all(self, input_layer_name, output_layer_name):
        print("### ", input_layer_name, output_layer_name)

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(gpkg, input_layer_name)
        output_layer_path = "{}|layername={}".format(gpkg, output_layer_name)
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

    def _test_skip_some(self, input_layer_name, output_layer_name):
        print("### ", input_layer_name, output_layer_name)

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(gpkg, input_layer_name)
        output_layer_path = "{}|layername={}".format(gpkg, output_layer_name)
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

    def _test_skip_none(self, input_layer_name, output_layer_name):
        print("### ", input_layer_name, output_layer_name)

        gpkg = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(gpkg, input_layer_name)
        output_layer_path = "{}|layername={}".format(gpkg, output_layer_name)
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