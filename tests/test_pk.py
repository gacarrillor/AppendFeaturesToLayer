import nose2

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import (CommonTests,
                         APPENDED_COUNT, UPDATED_COUNT, SKIPPED_COUNT, get_test_file_copy_path, get_test_path)

start_app()


class TestTablePK(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up TestTablePK')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()
        self.common = CommonTests()

    def test_append_update_PKs(self):
        print('\nINFO: Validating avoiding to set/update PKs...')
        source_gpkg = get_test_file_copy_path('source_pk.gpkg')
        gpkg = get_test_file_copy_path('bd_pk.gpkg')

        input_layer_name, output_layer_name = 'source', 'tiporegla'
        input_layer = QgsVectorLayer("{}|layername={}".format(source_gpkg, input_layer_name), 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer("{}|layername={}".format(gpkg, output_layer_name), 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        # Let's create a feature with T_Id=1, we'll update its
        # corresponding feature (which has a T_Id=100) successfully
        f = QgsFeature(output_layer.fields())
        f.setAttribute("T_Id", 1)
        f.setAttribute("codigo", "R0001")
        f.setAttribute("descripcion", "ABC")
        self.assertTrue(output_layer.dataProvider().addFeatures([f]))

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_COUNT], 3)
        self.assertIsNone(res[SKIPPED_COUNT])

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down TestTablePK')
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()
