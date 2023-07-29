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
                         get_qgis_gpkg_layer,
                         APPENDED_COUNT,
                         UPDATED_COUNT,
                         SKIPPED_COUNT)

start_app()


class TestTableTable(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_table_table')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()
        self.common = CommonTests()

    def test_copy_all(self):
        print('\nINFO: Validating table-table copy&paste all...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_all('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

    def test_copy_selected(self):
        print('\nINFO: Validating table-table copy&paste selected...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_selected('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    def test_update(self):
        print('\nINFO: Validating table-table update...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        self.common._test_update('source_table', output_layer, layer_path)

    def test_skip_all(self):
        print('\nINFO: Validating table-table skip (all) duplicate features...')
        self.common._test_skip_all('source_table', 'target_table')

    def test_skip_some(self):
        print('\nINFO: Validating table-table skip (some) duplicate features...')
        self.common._test_skip_some('source_table', 'target_table')

    def test_skip_none(self):
        print('\nINFO: Validating table-table skip (none) duplicate features...')
        self.common._test_skip_none('source_table', 'target_table')

    def test_skip_update_1_m(self):
        print('\nINFO: Validating table-table skip/update 1:m...')
        # Let's copy twice the same 2 features to end up with 1:m (twice)
        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_all('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        output_path = layer.source().split('|')[0]

        res = self.common._test_copy_all('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 2)

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': "{}|layername={}".format(output_path, 'source_table'),
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertIsNone(res[UPDATED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 4)

        # And counts for update action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': "{}|layername={}".format(output_path, 'source_table'),
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 2})  # Update

        self.assertEqual(layer.featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_COUNT], 4)
        self.assertIsNone(res[SKIPPED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Update

    def test_skip_update_m_1(self):
        print('\nINFO: Validating table-table skip/update m:1...')
        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_all('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']
        output_path = layer.source().split('|')[0]

        # Let's give both source features the same name to have an m:1 scenario
        input_layer_path = "{}|layername={}".format(output_path, 'source_table')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        input_layer.dataProvider().changeAttributeValues({2: {1: 'abc'}})  # name --> abc

        s = set()
        s.update([f['name'] for f in input_layer.getFeatures()])
        self.assertEqual(len(s), 1)  # Have really both features the same name?

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertIsNone(res[UPDATED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 2)

        # And counts for update action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 2})  # Update

        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_COUNT], 1)  # We do 2 updates on a single feature, the count is 1!
        self.assertIsNone(res[SKIPPED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Update

    def test_skip_different_field_types_can_convert(self):
        print('\nINFO: Validating table-table skip different field types can convert...')

        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_selected('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        # Let's overwrite the target feature to have a float as string
        layer.dataProvider().changeAttributeValues({next(layer.getFeatures()).id(): {1: "3.1416"}})  # name --> "3.1416"

        check_list_values = [f['name'] for f in layer.getFeatures()]
        self.assertEqual(len(check_list_values), 1)
        self.assertEqual(check_list_values[0], "3.1416")

        input_layer_path = "{}|layername={}".format(layer_path, 'source_table')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'real_value',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertIsNone(res[UPDATED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 1)

        # Now test the reverse
        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_selected('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        # Let's overwrite the target feature to have a float as string
        input_layer_path = "{}|layername={}".format(layer_path, 'source_table')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        input_layer.dataProvider().changeAttributeValues({1: {1: "3.1416"}})  # name --> "3.1416"

        check_list_values = [f['name'] for f in input_layer.getFeatures()]
        self.assertEqual(len(check_list_values), 2)
        self.assertEqual(check_list_values, ["3.1416", "def"])

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'real_value',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertIsNone(res[UPDATED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 1)

    def test_skip_different_field_types_cannot_convert(self):
        print('\nINFO: Validating table-table skip different field types cannot convert...')

        # Since it can't convert between types (and since types are different), no duplicates can be found, so
        # everything is appended.

        output_layer, layer_path = get_qgis_gpkg_layer('target_table')
        res = self.common._test_copy_selected('source_table', output_layer, layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        output_path = layer.source().split('|')[0]

        # Let's overwrite the target feature to have a float as string
        layer.dataProvider().changeAttributeValues({next(layer.getFeatures()).id(): {1: "3.1416"}})  # name --> "3.1416"

        check_list_values = [f['name'] for f in layer.getFeatures()]
        self.assertEqual(len(check_list_values), 1)
        self.assertEqual(check_list_values[0], "3.1416")

        input_layer_path = "{}|layername={}".format(output_path, 'source_table')
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'real_value',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'date_value',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 0)

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_table_table')
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()
