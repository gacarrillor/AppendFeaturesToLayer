from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import (CommonTests,
                         get_pg_conn,
                         get_qgis_pg_layer,
                         get_qgis_gpkg_layer,
                         get_test_file_copy_path,
                         prepare_pg_db_1,
                         PG_BD_1,
                         APPENDED_COUNT,
                         UPDATED_FEATURE_COUNT,
                         SKIPPED_COUNT,
                         drop_all_tables,
                         truncate_table,
                         JSON_VALUE_1,
                         JSON_VALUE_2)

start_app()


class TestPGTablePGTable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\nINFO: Set up test_table_table')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        cls.plugin = AppendFeaturesToLayerPlugin(get_iface)
        cls.plugin.initGui()
        cls.common = CommonTests()
        prepare_pg_db_1()

    def test_copy_all(self):
        print('\nINFO: Validating gpkg table - pg table copy&paste all...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self.common._test_copy_all('source_table', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

    def _test_copy_all_json_to_json(self):
        print('\nINFO: Validating gpkg table - pg table copy&paste all (JSON to JSON)...')
        conn = get_pg_conn(PG_BD_1)
        self.assertIsNotNone(conn)
        cur = conn.cursor()
        cur.execute("""ALTER TABLE target_table ADD COLUMN json_value JSON;""")
        cur.close()
        conn.commit()

        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)
        self.assertTrue(pg_layer.fields().indexOf("json_value") != -1)

        res = self.common._test_copy_all('source_table', pg_layer)  # This is failing --> QGIS bug
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

        expected_json_values = {'abc': JSON_VALUE_1, 'def': JSON_VALUE_2}

        for f in layer.getFeatures():
            self.assertEqual(f['json_value'], expected_json_values[f['name']])

        # We don't necessarily want the JSON_field populated in other tests
        # Specially, because of a bug in QGIS when pasting multiple features (JSON to JSON)
        # So, remove the just created JSON field after this specific test
        cur = conn.cursor()
        cur.execute("""ALTER TABLE target_table DROP COLUMN json_value;""")
        cur.close()
        conn.commit()

    def test_copy_selected_json_to_json(self):
        print('\nINFO: Validating gpkg table - pg table copy&paste selected (JSON to JSON)...')
        conn = get_pg_conn(PG_BD_1)
        self.assertIsNotNone(conn)
        cur = conn.cursor()
        cur.execute("""ALTER TABLE target_table ADD COLUMN json_value JSON;""")
        cur.close()
        conn.commit()

        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)
        self.assertTrue(pg_layer.fields().indexOf("json_value") != -1)

        res = self.common._test_copy_selected('source_table', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        expected_json_values = {'abc': JSON_VALUE_1, 'def': JSON_VALUE_2}

        for f in layer.getFeatures():
            self.assertEqual(f['json_value'], expected_json_values[f['name']])

        # We don't necessarily want the JSON_field populated in other tests
        # Specially, because of a bug in QGIS when pasting multiple features (JSON to JSON)
        # So, remove the just created JSON field after this specific test
        cur = conn.cursor()
        cur.execute("""ALTER TABLE target_table DROP COLUMN json_value;""")
        cur.close()
        conn.commit()

    def test_copy_all_string_to_json(self):
        print('\nINFO: Validating gpkg table - pg table copy&paste all (String to JSON)...')
        conn = get_pg_conn(PG_BD_1)
        self.assertIsNotNone(conn)
        cur = conn.cursor()
        cur.execute("""ALTER TABLE target_table ADD COLUMN text_value JSON;""")
        cur.close()
        conn.commit()

        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)
        self.assertTrue(pg_layer.fields().indexOf("text_value") != -1)

        res = self.common._test_copy_all('source_table', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

        expected_json_values = {'abc': JSON_VALUE_1, 'def': JSON_VALUE_2}

        for f in layer.getFeatures():
            self.assertEqual(f['text_value'], expected_json_values[f['name']])

    def test_copy_selected(self):
        print('\nINFO: Validating gpkg table - pg table copy&paste selected...')
        res = self.common._test_copy_selected('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    def test_update(self):
        print('\nINFO: Validating gpkg table - pg table update...')
        # Test for issue #10 (ChangeGeometries is False, but ChangeAttributeValues is True for target_table)
        self.common._test_update('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_all(self):
        print('\nINFO: Validating gpkg table - pg table skip (all) duplicate features...')
        self.common._test_skip_all('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_some(self):
        print('\nINFO: Validating gpkg table - pg table skip (some) duplicate features...')
        self.common._test_skip_some('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_none(self):
        print('\nINFO: Validating gpkg table - pg table skip (none) duplicate features...')
        self.common._test_skip_none('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_update_1_m(self):
        print('\nINFO: Validating gpkg table - pg table skip/update 1:m...')
        # Let's copy twice the same 2 features to end up with 1:m (twice)
        output_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        self.common._test_copy_all('source_table', output_layer)
        res = self.common._test_copy_all('source_table', output_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 2)

        # Now let's check counts for skip action
        input_layer, layer_path = get_qgis_gpkg_layer('source_table')
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 4)

        # And counts for update action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 2})  # Update

        self.assertEqual(layer.featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 4)
        self.assertIsNone(res[SKIPPED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Update

    def test_skip_update_m_1(self):
        print('\nINFO: Validating gpkg table - pg table skip/update m:1...')
        output_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        res = self.common._test_copy_all('source_table', output_layer)

        # Let's give both source features the same name to have an m:1 scenario
        input_layer, layer_path = get_qgis_gpkg_layer('source_table')
        input_layer.dataProvider().changeAttributeValues({2: {1: 'abc'}})  # name --> abc

        s = set()
        s.update([f['name'] for f in input_layer.getFeatures()])
        self.assertEqual(len(s), 1)  # Have really both features the same name?

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(output_layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 2)

        # And counts for update action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 2})  # Update

        self.assertEqual(output_layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 1)  # We do 2 updates on a single feature, the count is 1!
        self.assertIsNone(res[SKIPPED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Update

    def test_skip_different_field_types_can_convert(self):
        print('\nINFO: Validating gpkg table - pg table skip different field types can convert...')

        output_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        input_layer, input_layer_path = get_qgis_gpkg_layer('source_table')
        res = self.common._test_copy_selected('source_table', output_layer, input_layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        # Let's overwrite the target feature to have a float as string
        layer.dataProvider().changeAttributeValues({next(layer.getFeatures()).id(): {1: "3.1416"}})  # name --> "3.1416"

        check_list_values = [f['name'] for f in layer.getFeatures()]
        self.assertEqual(len(check_list_values), 1)
        self.assertEqual(check_list_values[0], "3.1416")

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'real_value',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 1)

        # Now test the reverse
        output_layer = get_qgis_pg_layer(PG_BD_1, 'target_table', truncate=True)
        res = self.common._test_copy_selected('source_table', output_layer, input_layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        # Let's overwrite the source feature to have a float as string
        # input_layer_path = "{}|layername={}".format(layer_path, 'source_table')
        # input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
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
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 1)

    def test_skip_different_field_types_cannot_convert(self):
        print('\nINFO: Validating gpkg table - pg table skip different field types cannot convert...')

        # Since it can't convert between types (and since types are different), no duplicates can be found, so
        # everything is appended.
        output_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        input_layer, input_layer_path = get_qgis_gpkg_layer('source_table')
        res = self.common._test_copy_selected('source_table', output_layer, input_layer_path)
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

        # Now let's check counts for skip action
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'real_value',
                              'TARGET_LAYER': layer,
                              'TARGET_FIELD': 'date_value',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(layer.featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 0)

    @staticmethod
    def tearDown():
        truncate_table(PG_BD_1, 'target_table')

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down test_pg_table_pg_table')
        drop_all_tables()
        cls.plugin.unload()
