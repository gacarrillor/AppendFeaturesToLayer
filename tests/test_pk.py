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
                         APPENDED_COUNT,
                         UPDATED_COUNT,
                         SKIPPED_COUNT,
                         get_test_file_copy_path,
                         get_test_path,
                         get_qgis_pg_layer,
                         prepare_pg_db_1,
                         drop_all_tables,
                         PG_BD_1)

start_app()


class TestTablePK(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('\nINFO: Set up TestTablePK')
        from AppendFeaturesToLayer.append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
        cls.plugin = AppendFeaturesToLayerPlugin(get_iface)
        cls.plugin.initGui()
        cls.common = CommonTests()
        prepare_pg_db_1()

    def test_append_update_pks_gpkg(self):
        print('\nINFO: Validating avoiding to set/update PKs in GPKG...')
        source_gpkg = get_test_file_copy_path('source_pk.gpkg')  # fid, T_Id, codigo, descripcion
        gpkg = get_test_file_copy_path('bd_pk.gpkg')  # T_Id, T_Ili_Tid, codigo, descripcion, entidad

        input_layer_name, output_layer_name = 'source', 'tiporegla'
        input_layer = QgsVectorLayer("{}|layername={}".format(source_gpkg, input_layer_name), 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())
        output_layer = QgsVectorLayer("{}|layername={}".format(gpkg, output_layer_name), 'layer name', 'ogr')
        self.assertTrue(output_layer.isValid())
        QgsProject.instance().addMapLayers([input_layer, output_layer])

        # Let's create a feature with T_Id=1, we'll update its
        # corresponding feature (which has a T_Id=100 in the source) successfully
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

        # print([f.name() for f in output_layer.fields()])
        # print([f.attributes() for f in output_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in output_layer.getFeatures()], [1, 2, 3])  # Automatic PKs

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_COUNT], 3)  # Only 1 feature (and 1 attribute in that feature) is actually changed
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in output_layer.fields()])
        # print([f.attributes() for f in output_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in output_layer.getFeatures()], [1, 2, 3])  # We don't touch the automatic PKs

        # The only updated value
        self.assertEqual(output_layer.getFeature(1)["descripcion"], 'Los datos deben corresponder a su modelo')

    def test_append_update_pks_pg_serial_notnull(self):
        print('\nINFO: Validating avoiding to set/update PKs (serial, NOT NULL) in PG...')
        source_gpkg = get_test_file_copy_path('source_pk.gpkg')  # fid, T_Id, codigo, descripcion

        pg_layer = get_qgis_pg_layer(PG_BD_1, 'tipo_regla', truncate=True)  # T_Id, codigo, descripcion
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        input_layer_name = 'source'
        input_layer = QgsVectorLayer("{}|layername={}".format(source_gpkg, input_layer_name), 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, pg_layer])

        # Let's create a feature with T_Id=1, we'll update its
        # corresponding feature (which has a T_Id=100 in the source) successfully
        f = QgsFeature(pg_layer.fields())
        # f.setAttribute("T_Id", 1)  # We shouldn't force a PK here, since we've got a serial, which is automatic
        f.setAttribute("codigo", "R0001")
        f.setAttribute("descripcion", "ABC")
        self.assertTrue(pg_layer.dataProvider().addFeatures([f]))
        self.assertEqual(pg_layer.featureCount(), 1)
        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 2, 3])  # Automatic PKs

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_COUNT], 3)  # Only 1 feature (and 1 attribute in that feature) is actually changed
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 2, 3])  # We don't touch the automatic PKs

        # The only updated value
        self.assertEqual(pg_layer.getFeature(1)["descripcion"], 'Los datos deben corresponder a su modelo')

    def test_append_update_pks_pg_no_serial_notnull(self):
        print('\nINFO: Validating avoiding to set/update PKs (no serial, NOT NULL) in PG...')
        source_gpkg = get_test_file_copy_path('source_pk.gpkg')  # fid, T_Id, codigo, descripcion

        pg_layer = get_qgis_pg_layer(PG_BD_1, 'tipo_regla_no_serial', truncate=True)  # T_Id, codigo, descripcion
        self.assertTrue(pg_layer.isValid())
        self.assertEqual(pg_layer.featureCount(), 0)

        input_layer_name = 'source'
        input_layer = QgsVectorLayer("{}|layername={}".format(source_gpkg, input_layer_name), 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, pg_layer])

        # Let's create a feature with T_Id=1, we'll update its
        # corresponding feature (which has a T_Id=100 in the source) successfully
        f = QgsFeature(pg_layer.fields())
        f.setAttribute("T_Id", 1)
        f.setAttribute("codigo", "R0001")
        f.setAttribute("descripcion", "ABC")
        self.assertTrue(pg_layer.dataProvider().addFeatures([f]))
        self.assertEqual(pg_layer.featureCount(), 1)
        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 100, 101])  # Automatic PKs

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_COUNT], 3)  # Only 1 feature (and 1 attribute in that feature) is actually changed
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 100, 101])  # We don't touch the automatic PKs

        # # The only updated value
        self.assertEqual(pg_layer.getFeature(1)["descripcion"], 'Los datos deben corresponder a su modelo')

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down TestTablePK')
        drop_all_tables()
        cls.plugin.unload()


if __name__ == '__main__':
    nose2.main()
