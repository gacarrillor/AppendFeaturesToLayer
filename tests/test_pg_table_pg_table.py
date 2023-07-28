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

        self.common = CommonTests()

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

        res = self.common._test_copy_all('source_table', get_qgis_pg_layer('db1', 'target_table'))
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

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
