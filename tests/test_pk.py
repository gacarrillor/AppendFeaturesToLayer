from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProject,
                       QgsFeature,
                       QgsFeatureRequest)
from qgis.testing import unittest, start_app
from qgis.testing.mocked import get_iface

import processing

from tests.utils import (CommonTests,
                         APPENDED_COUNT,
                         UPDATED_FEATURE_COUNT,
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
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
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
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 3)  # Only 1 feature (and 1 attribute in that feature) is actually changed
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in output_layer.fields()])
        # print([f.attributes() for f in output_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in output_layer.getFeatures()], [1, 2, 3])  # We don't touch the automatic PKs

        # The only updated value
        self.assertEqual(output_layer.getFeature(1)["descripcion"], 'Los datos deben corresponder a su modelo')

        # Finally, let's create a new feature in source and run on UPDATE mode.
        # We check here that we don't set the target PK (T_Id) field, even for new (i.e.,
        # non-duplicate) features, but let the provider calculate the new PK instead.
        f = QgsFeature(input_layer.fields())
        f.setAttribute("T_Id", 110)
        f.setAttribute("codigo", "R0010")
        f.setAttribute("descripcion", "ZYX")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 1)  # The new source feature which had T_Id=110
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 3)  # 3 matching features counted as UPDATED
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in output_layer.fields()])
        # print([f.attributes() for f in output_layer.getFeatures()])

        # It's the provider that creates the PK (T_Id),
        # so we don't see the 110 from the appended feature!
        self.assertEqual([f["T_Id"] for f in output_layer.getFeatures()], [1, 2, 3, 4])

        # The only appended value
        self.assertEqual(output_layer.getFeature(4)["descripcion"], 'ZYX')

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
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
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
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 3)  # Only 1 feature (and 1 attribute in that feature) is actually changed
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 2, 3])  # We don't touch the automatic PKs

        # The only updated value
        self.assertEqual(pg_layer.getFeature(1)["descripcion"], 'Los datos deben corresponder a su modelo')

        # Finally, let's create a new feature in source and run on UPDATE mode.
        # We check here that we don't set the target PK (T_Id) field, even for new (i.e.,
        # non-duplicate) features, but let the provider calculate the new PK instead.
        f = QgsFeature(input_layer.fields())
        f.setAttribute("T_Id", 110)
        f.setAttribute("codigo", "R0010")
        f.setAttribute("descripcion", "ZYX")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 1)  # The new source feature which had T_Id=110
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 3)  # 3 matching features counted as UPDATED
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])

        # It's the provider that creates the PK (T_Id),
        # so we don't see the 110 from the appended feature!
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 2, 3, 4])

        # The only appended value
        self.assertEqual(pg_layer.getFeature(4)["descripcion"], 'ZYX')

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
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 100, 101])  # Non-automatic PKs

        # Check that our ABC description is still there (will be updated in the next run)
        self.assertEqual(pg_layer.getFeature(1)["descripcion"], 'ABC')

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 3)  # Only 1 feature (and 1 attribute in that feature) is actually changed
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])

        # PKs are not changed, i.e., T_Id 1 remains being 1, in spite of having
        # a matching duplicate feature (codigo=R0001) from source with T_id=100
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 100, 101])

        # The only updated value
        self.assertEqual(pg_layer.getFeature(1)["descripcion"], 'Los datos deben corresponder a su modelo')

        # Finally, let's create a new feature in source and run on UPDATE mode.
        # We check here that we don't update the target PK (T_Id) field for duplicate features,
        # BUT we do set the target PK from new (i.e., non-duplicate) features.
        f = QgsFeature(input_layer.fields())
        f.setAttribute("T_Id", 110)
        f.setAttribute("codigo", "R0010")
        f.setAttribute("descripcion", "ZYX")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'codigo',
                              'TARGET_LAYER': pg_layer,
                              'TARGET_FIELD': 'codigo',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 1)  # The new source feature which had T_Id=110
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 3)  # 3 matching features counted as UPDATED
        self.assertIsNone(res[SKIPPED_COUNT])

        # print([f.name() for f in pg_layer.fields()])
        # print([f.attributes() for f in pg_layer.getFeatures()])

        # Since this time the target PK is not automatic, for non-duplicate features
        # we take it from the source, so we have the 110 from the appended feature!
        self.assertEqual([f["T_Id"] for f in pg_layer.getFeatures()], [1, 100, 101, 110])

        # The only appended value
        self.assertEqual(pg_layer.getFeature(110)["descripcion"], 'ZYX')

    def test_append_update_pks_pg_uuid_notnull(self):
        print('\nINFO: Validating to set/update PKs (UUID, NOT NULL) in PG...')

        # Create empty input layer
        input_layer = QgsVectorLayer("Point?crs=epsg:3116&field=fid:integer&field=T_Id:string&field=codigo:string&field=descripcion:string", "uuid-layer", "memory")
        self.assertTrue(input_layer.isValid())

        # Get target layer with UUID PK
        target_layer = get_qgis_pg_layer(PG_BD_1, 'tipo_regla_uuid', truncate=True)  # T_Id, codigo, descripcion
        self.assertTrue(target_layer.isValid())
        self.assertEqual(target_layer.featureCount(), 0)

        QgsProject.instance().addMapLayers([input_layer, target_layer])

        # Create two features on the target. One with and one without a UUID
        # We pass the uuids to be able to playe with them.
        f = QgsFeature(target_layer.fields())
        uuid_1 = '15431753-059f-4c23-ba60-0e0fc0b28fa5'
        f.setAttribute("T_Id", uuid_1)
        f.setAttribute("codigo", "R0001")
        f.setAttribute("descripcion", "ABC")
        self.assertTrue(target_layer.dataProvider().addFeatures([f]))
        self.assertEqual(target_layer.featureCount(), 1)
   
        f = QgsFeature(target_layer.fields())
        f.setAttribute("codigo", "R0002")
        f.setAttribute("descripcion", "DEF")
        self.assertTrue(target_layer.dataProvider().addFeatures([f]))
        self.assertEqual(target_layer.featureCount(), 2)

        # get the generated UUID of the second feature
        uuids_in_target = [f["T_Id"] for f in target_layer.getFeatures()]
        self.assertEqual(len(uuids_in_target), 2) 
        uuid_2 = list(set(uuids_in_target) - {uuid_1})[0]
        self.assertIsNotNone(uuid_2)

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF

        # Create two features on the input. One with and one without a UUID
        f = QgsFeature(input_layer.fields())
        uuid_3 = '12616fa9-f8f8-4746-b5e9-302b387cdb8f'
        f.setAttribute("T_Id", uuid_3) 
        f.setAttribute("codigo", "R0003") 
        f.setAttribute("descripcion", "GHI")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))

        f = QgsFeature(input_layer.fields())
        f.setAttribute("codigo", "R0004") 
        f.setAttribute("descripcion", "JKL")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))

        # Status in the input layer:
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: None, codigo: R0004, descripcion: JKL
        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF

        # Expected is the adding of two features, one with the given and the other with the generated UUID 
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': target_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT]) 
        self.assertIsNone(res[SKIPPED_COUNT])

        # get the generated UUID of the fourth feature
        uuids_in_target = [f["T_Id"] for f in target_layer.getFeatures()]
        self.assertEqual(len(uuids_in_target), 4) 
        uuid_4 = list(set(uuids_in_target) - {uuid_1, uuid_2, uuid_3})[0]
        self.assertIsNotNone(uuid_4)

        # Status in the input layer:
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: None, codigo: R0004, descripcion: JKL

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_4, codigo: R0004, descripcion: JKL

        # Now we do it again, and now it creates the two features again, generating two new UUIDs (because caring itself for uniqueness)
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': target_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 6)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT]) 
        self.assertIsNone(res[SKIPPED_COUNT])

        # get the generated UUID of the fifth and the sixth feature
        uuids_in_target = [f["T_Id"] for f in target_layer.getFeatures()]
        self.assertEqual(len(uuids_in_target), 6) 
        uuid_5 = list(set(uuids_in_target) - {uuid_1, uuid_2, uuid_3, uuid_4})[0]
        self.assertIsNotNone(uuid_5)
        uuid_6 = list(set(uuids_in_target) - {uuid_1, uuid_2, uuid_3, uuid_4, uuid_5})[0]
        self.assertIsNotNone(uuid_6)

        # Status in the input layer:
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: None, codigo: R0004, descripcion: JKL

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_4, codigo: R0004, descripcion: JKL
        # T_Id: uuid_5, codigo: R0003, descripcion: GHI
        # T_Id: uuid_6, codigo: R0004, descripcion: JKL

        # When we would skip, the one with the existing UUID (uuid_3) will be skipped, but the one with None in the source (R0004)
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'T_Id',
                              'TARGET_LAYER': target_layer,
                              'TARGET_FIELD': 'T_Id',
                              'ACTION_ON_DUPLICATE': 1})  # Skip duplicates

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 7)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT]) 
        self.assertEqual(res[SKIPPED_COUNT], 1)

        # get the generated UUID of the fifth feature
        uuids_in_target = [f["T_Id"] for f in target_layer.getFeatures()]
        self.assertEqual(len(uuids_in_target), 7) 
        uuid_7 = list(set(uuids_in_target) - {uuid_1, uuid_2,uuid_3, uuid_4, uuid_5,uuid_6})[0]
        self.assertIsNotNone(uuid_7)

        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: None, codigo: R0004, descripcion: JKL

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_4, codigo: R0004, descripcion: JKL
        # T_Id: uuid_5, codigo: R0003, descripcion: GHI
        # T_Id: uuid_6, codigo: R0004, descripcion: JKL
        # T_Id: uuid_7, codigo: R0004, descripcion: JKL

        # let's fix the mess
        # we remove the feature 4 from the input
        request = QgsFeatureRequest()
        request.setFilterExpression(f'"codigo" = \'R0004\'')
        R0004_feature = list(input_layer.getFeatures(request))[0]
        input_layer.dataProvider().deleteFeatures([R0004_feature.id()])
        # we append proper features for 5, 6 and 7 and update them
        f = QgsFeature(input_layer.fields())
        f.setAttribute("T_Id", uuid_5) 
        f.setAttribute("codigo", "R0005") 
        f.setAttribute("descripcion", "MNO")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))
        f = QgsFeature(input_layer.fields())
        f.setAttribute("T_Id", uuid_6) 
        f.setAttribute("codigo", "R0006") 
        f.setAttribute("descripcion", "PQR")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))
        f = QgsFeature(input_layer.fields())
        f.setAttribute("T_Id", uuid_7) 
        f.setAttribute("codigo", "R0007") 
        f.setAttribute("descripcion", "STU")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))
        
        # Status in the input layer:
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_5, codigo: R0005, descripcion: MNO
        # T_Id: uuid_6, codigo: R0006, descripcion: PQR
        # T_Id: uuid_7, codigo: R0007, descripcion: STU

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_4, codigo: R0004, descripcion: JKL
        # T_Id: uuid_5, codigo: R0003, descripcion: GHI
        # T_Id: uuid_6, codigo: R0004, descripcion: JKL
        # T_Id: uuid_7, codigo: R0004, descripcion: JKL

        # And we perform an update for the duplicate considering the T_Id (UUID)
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'T_Id',
                              'TARGET_LAYER': target_layer,
                              'TARGET_FIELD': 'T_Id',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 7)
        self.assertEqual(res[APPENDED_COUNT], 0) # No new appended (all already exist)
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 4) # The four others are updated, although one (R0003)without changes
        self.assertIsNone(res[SKIPPED_COUNT])

        uuids_in_target = [f["T_Id"] for f in target_layer.getFeatures()]
        self.assertEqual(len(uuids_in_target), 7) 
        self.assertEqual(set(uuids_in_target), {uuid_1, uuid_2,uuid_3, uuid_4, uuid_5,uuid_6, uuid_7})
        codigos_in_target = [f["codigo"] for f in target_layer.getFeatures()]
        self.assertEqual( set(codigos_in_target), {'R0001', 'R0002', 'R0003', 'R0004', 'R0005', 'R0006', 'R0007'})

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_4, codigo: R0004, descripcion: JKL
        # T_Id: uuid_5, codigo: R0005, descripcion: MNO
        # T_Id: uuid_6, codigo: R0006, descripcion: PQR
        # T_Id: uuid_7, codigo: R0007, descripcion: STU

        # Now we add a new one with a new UUID, which should be added without problems
        f = QgsFeature(input_layer.fields())
        uuid_8 = 'bae27e96-bffc-4b27-9cdc-162731043293'
        f.setAttribute("T_Id", uuid_8) 
        f.setAttribute("codigo", "R0008") 
        f.setAttribute("descripcion", "VWX")
        self.assertTrue(input_layer.dataProvider().addFeatures([f]))

        # And we perform an update for the duplicate considering the T_Id (UUID)
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'T_Id',
                              'TARGET_LAYER': target_layer,
                              'TARGET_FIELD': 'T_Id',
                              'ACTION_ON_DUPLICATE': 2})  # UPDATE

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 8)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 4) # The four others are updated, although without changes
        self.assertIsNone(res[SKIPPED_COUNT])

        uuids_in_target = [f["T_Id"] for f in target_layer.getFeatures()]
        self.assertEqual(len(uuids_in_target), 8) 
        self.assertEqual(set(uuids_in_target), {uuid_1, uuid_2,uuid_3, uuid_4, uuid_5,uuid_6, uuid_7, uuid_8})
        codigos_in_target = [f["codigo"] for f in target_layer.getFeatures()]
        self.assertEqual( set(codigos_in_target), {'R0001', 'R0002', 'R0003', 'R0004', 'R0005', 'R0006', 'R0007', 'R0008'})

        # Status in the target layer:
        # T_Id: uuid_1, codigo: R0001, descripcion: ABC
        # T_Id: uuid_2, codigo: R0002, descripcion: DEF
        # T_Id: uuid_3, codigo: R0003, descripcion: GHI
        # T_Id: uuid_4, codigo: R0004, descripcion: JKL
        # T_Id: uuid_5, codigo: R0005, descripcion: MNO
        # T_Id: uuid_6, codigo: R0006, descripcion: PQR
        # T_Id: uuid_7, codigo: R0007, descripcion: STU
        # T_Id: uuid_8, codigo: R0008, descripcion: VWX

    @classmethod
    def tearDownClass(cls):
        print('INFO: Tear down TestTablePK')
        drop_all_tables()
        cls.plugin.unload()
