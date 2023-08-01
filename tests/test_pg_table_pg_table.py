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
                         prepare_pg_db_1,
                         PG_BD_1,
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

        prepare_pg_db_1()

    def test_copy_all(self):
        print('\nINFO: Validating pg table - pg table copy&paste all...')
        pg_layer = get_qgis_pg_layer(PG_BD_1, 'target_table')
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        res = self.common._test_copy_all('source_table', pg_layer)
        layer = res['TARGET_LAYER']
        self.assertEqual(layer.featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)

    def test_copy_selected(self):
        print('\nINFO: Validating pg table - pg table copy&paste selected...')
        res = self.common._test_copy_selected('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))
        layer = res['TARGET_LAYER']

        self.assertEqual(layer.featureCount(), 1)
        self.assertEqual(res[APPENDED_COUNT], 1)

    def test_update(self):
        print('\nINFO: Validating pg table - pg table update...')
        self.common._test_update('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_all(self):
        print('\nINFO: Validating pg table - pg table skip (all) duplicate features...')
        self.common._test_skip_all('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_some(self):
        print('\nINFO: Validating pg table - pg table skip (some) duplicate features...')
        self.common._test_skip_some('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    def test_skip_none(self):
        print('\nINFO: Validating pg table - pg table skip (none) duplicate features...')
        self.common._test_skip_none('source_table', get_qgis_pg_layer(PG_BD_1, 'target_table'))

    @staticmethod
    def tearDown():
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute("TRUNCATE target_table;")
        cur.close()
        conn.commit()

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
