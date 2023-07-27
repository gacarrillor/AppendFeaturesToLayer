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
                         get_pg_conn,
                         get_qgis_pg_layer,
                         get_test_file_copy_path,
                         APPENDED_COUNT,
                         UPDATED_COUNT,
                         SKIPPED_COUNT)

start_app()


class TestPGTablePGTable(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('\nINFO: Set up test_table_table')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        self.plugin = AppendFeaturesToLayerPlugin(get_iface)
        self.plugin.initGui()

    def test_copy_all(self):
        print('\nINFO: Validating table-table copy&paste all...')
        conn = get_pg_conn()
        self.assertIsNotNone(conn, "PG connection to db1 shouldn't be None!")

        if conn:
            cur = conn.cursor()
            cur.execute('CREATE TABLE target_table(id serial NOT NULL, name text, real_value real, date_value timestamp, exra_value text);')
            cur.execute('ALTER TABLE target_table ADD CONSTRAINT pk_target_table PRIMARY KEY (id);')
            cur.close()
            conn.commit()

        pg_layer = get_qgis_pg_layer()
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self._test_copy_all('source_table', 'target_table')
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

    def _test_copy_all(self, input_layer_name, output_layer_name, input_path=None):
        if input_path is None:
            input_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        output = get_qgis_pg_layer('db1', output_layer_name)

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': "{}|layername={}".format(input_path, input_layer_name),
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertTrue(output.isValid())
        self.assertIsNone(res[UPDATED_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])
        return res

    @classmethod
    def tearDownClass(self):
        print('INFO: Tear down test_pg_table_pg_table')
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute("DROP TABLE target_table;")
        cur.close()
        conn.commit()
        self.plugin.unload()


if __name__ == '__main__':
    nose2.main()
