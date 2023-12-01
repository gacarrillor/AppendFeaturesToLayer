import os
import psycopg2
import tempfile
import unittest
from shutil import copyfile

from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsProject,
                       QgsProcessingFeatureSourceDefinition,
                       QgsFeature,
                       QgsDataSourceUri)
from qgis.analysis import QgsNativeAlgorithms
import qgis.utils

import processing

from qgis.testing.mocked import get_iface

APPENDED_COUNT = 'APPENDED_COUNT'
UPDATED_FEATURE_COUNT = 'UPDATED_FEATURE_COUNT'
UPDATED_ONLY_GEOMETRY_COUNT = 'UPDATED_ONLY_GEOMETRY_COUNT'
SKIPPED_COUNT = 'SKIPPED_COUNT'

PG_BD_1 = "db1"

TEST_DIR = tempfile.mkdtemp()  # To send all temporal copies there


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

    global TEST_DIR
    dst_path = os.path.join(TEST_DIR, next(tempfile._get_candidate_names()) + dst_path[1])
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


def get_pg_connection_uri(dict_conn, level=1):
    uri = []
    uri += ['host={}'.format(dict_conn['host'])]
    uri += ['port={}'.format(dict_conn['port'])]
    if dict_conn['username']:
        uri += ['user={}'.format(dict_conn['username'])]
    if dict_conn['password']:
        uri += ['password={}'.format(dict_conn['password'])]
    if level == 1 and dict_conn['database']:
        uri += ['dbname={}'.format(dict_conn['database'])]
    else:
        # It is necessary to define the database name for listing databases
        # PostgreSQL uses the db 'postgres' by default and it cannot be deleted, so we use it as last resort
        uri += ["dbname={}".format('postgres')]

    return ' '.join(uri)


def get_pg_conn(db=PG_BD_1):
    dict_conn = {'host': 'postgres',
                 'port': 5432,
                 'username': 'user1',
                 'password': 'pass1',
                 'database': db}
    uri = get_pg_connection_uri(dict_conn)
    conn = None
    try:
        conn = psycopg2.connect(uri)
    except (psycopg2.OperationalError, psycopg2.ProgrammingError) as e:
        print("ERROR: Could not open PG DB connection! Details: {}".format(e))

    return conn


def get_qgis_pg_layer(db=PG_BD_1, table='target_table', geom_column=None, truncate=False):
    uri = QgsDataSourceUri()

    # set host name, port, database name, username and password
    uri.setConnection("postgres", "5432", db, "user1", "pass1")

    # set database schema, table name, geometry column and optionally
    # subset (WHERE clause)
    uri.setDataSource("public", table, geom_column, aKeyColumn="id")

    layer = QgsVectorLayer(uri.uri(), table, "postgres")
    if truncate:
        layer.dataProvider().truncate()

    return layer


def prepare_pg_db_1():
    conn = get_pg_conn(PG_BD_1)
    if conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS target_table(id serial NOT NULL, name text, real_value double precision, date_value timestamp, exra_value text);
            ALTER TABLE target_table ADD CONSTRAINT pk_target_table PRIMARY KEY (id);

            CREATE TABLE IF NOT EXISTS target_simple_lines(id serial NOT NULL, geom geometry(Linestring,3116) NULL, name text);
            ALTER TABLE target_simple_lines ADD CONSTRAINT pk_target_simple_lines PRIMARY KEY (id);

            CREATE TABLE IF NOT EXISTS target_simple_polygons(id serial NOT NULL, geom geometry(Polygon,3116) NULL, name text, real_value double precision, date_value timestamp, exra_value text);
            ALTER TABLE target_simple_polygons ADD CONSTRAINT pk_target_simple_polygons PRIMARY KEY (id);

            CREATE TABLE IF NOT EXISTS target_multi_polygons(id serial NOT NULL, geom geometry(MultiPolygon,3116) NULL, name text, real_value double precision, date_value timestamp, exra_value text);
            ALTER TABLE target_multi_polygons ADD CONSTRAINT pk_target_multi_polygons PRIMARY KEY (id);

            CREATE TABLE IF NOT EXISTS tipo_regla("T_Id" serial NOT NULL, codigo text, descripcion text);
            ALTER TABLE tipo_regla ADD CONSTRAINT pk_tipo_regla PRIMARY KEY ("T_Id");

            CREATE TABLE IF NOT EXISTS tipo_regla_no_serial("T_Id" integer NOT NULL, codigo text, descripcion text);
            ALTER TABLE tipo_regla_no_serial ADD CONSTRAINT pk_tipo_regla_no_serial PRIMARY KEY ("T_Id");
        """)
        cur.close()
        conn.commit()


def truncate_table(db=PG_BD_1, table='target_table'):
    conn = get_pg_conn(db)
    cur = conn.cursor()
    cur.execute(f"TRUNCATE {table};")
    cur.close()
    conn.commit()


def drop_all_tables(db=PG_BD_1):
    conn = get_pg_conn(db)
    if conn:
        cur = conn.cursor()
        cur.execute("""
        ALTER TABLE target_table DROP CONSTRAINT IF EXISTS pk_target_table;
        DROP TABLE target_table;
        ALTER TABLE target_simple_lines DROP CONSTRAINT IF EXISTS pk_target_simple_lines;
        DROP TABLE target_simple_lines;
        ALTER TABLE target_simple_polygons DROP CONSTRAINT IF EXISTS pk_target_simple_polygons;
        DROP TABLE target_simple_polygons;
        ALTER TABLE target_multi_polygons DROP CONSTRAINT IF EXISTS pk_target_multi_polygons;
        DROP TABLE target_multi_polygons;
        ALTER TABLE tipo_regla DROP CONSTRAINT IF EXISTS pk_tipo_regla;
        DROP TABLE tipo_regla;
        ALTER TABLE tipo_regla_no_serial DROP CONSTRAINT IF EXISTS pk_tipo_regla_no_serial;
        DROP TABLE tipo_regla_no_serial;
        """)
        cur.close()
        conn.commit()


def get_qgis_gpkg_layer(layer_name, layer_path=None):
    if layer_path is None:
        # Get the layer from a DB copy
        layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

    return QgsVectorLayer("{}|layername={}".format(layer_path, layer_name), "", "ogr"), layer_path


def real_values_are_equal(r1, r2, precision):
    """
    Example: 3.1415996 and 3.1416
    """
    return r1 - r2 < float(f'1e-0{precision}')



class CommonTests(unittest.TestCase):
    """ Utility functions """

    def _test_copy_all(self, input_layer_name, output_layer, input_layer_path=None):
        if input_layer_path is None:
            # Note that when input and output are in the same DB, input_layer_path should be passed as arg
            # so that no other temp file is generated.
            input_layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': "{}|layername={}".format(input_layer_path, input_layer_name),
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertTrue(output_layer.isValid())
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])
        return res

    def _test_copy_selected(self, input_layer_name, output_layer, input_layer_path=None, select_id=1):
        if input_layer_path is None:
            # Note that when input and output are in the same DB, input_layer_path should be passed as arg
            # so that no other temp file is generated.
            input_layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(input_layer_path, input_layer_name)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, output_layer])

        input_layer.select(select_id)  # fid=1

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': QgsProcessingFeatureSourceDefinition(input_layer_path, True),
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        return res

    def _test_update(self, input_layer_name, output_layer, input_layer_path=None):
        if input_layer_path is None:
            # Note that when input and output are in the same DB, input_layer_path should be passed as arg
            # so that no other temp file is generated.
            input_layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(input_layer_path, input_layer_name)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, output_layer])

        # First, let's have some records to update
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # Let's modify values in the input layer to attempt to update later in the output via our plugin
        input_layer.dataProvider().changeAttributeValues({1: {3: 30}})  # real_value --> 30

        # Create another record in input_layer to test that not-found records are appended
        new_feature = QgsFeature()
        new_feature.setAttributes([5, 'ABC', 1, 2.0])
        input_layer.dataProvider().addFeatures([new_feature])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 2})  # Update

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertEqual(res[UPDATED_FEATURE_COUNT], 2)
        self.assertIsNone(res[SKIPPED_COUNT])  # This is None because ACTION_ON_DUPLICATE is Update

        feature = next(output_layer.getFeatures('"name"=\'abc\''))
        self.assertEqual(feature['real_value'], 30)

        feature = next(output_layer.getFeatures('"name"=\'ABC\''))
        self.assertEqual(feature['real_value'], 2.0)

    def _test_skip_all(self, input_layer_name, output_layer, input_layer_path=None):
        if input_layer_path is None:
            # Note that when input and output are in the same DB, input_layer_path should be passed as arg
            # so that no other temp file is generated.
            input_layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(input_layer_path, input_layer_name)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, output_layer])

        # First, let's have some records to be able to test the skip mode
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # Let's modify values in the input layer to be able to check that
        # these new values are never transfererd to the output layer
        input_layer.dataProvider().changeAttributeValues({1: {3: 30}})  # real_value --> 30
        input_layer.dataProvider().changeAttributeValues({2: {3: 50}})  # real_value --> 50

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 0)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 2)

        feature = next(output_layer.getFeatures('"name"=\'abc\''))
        self.assertTrue(real_values_are_equal(feature['real_value'], 3.1416, 5))

        feature = next(output_layer.getFeatures('"name"=\'def\''))
        self.assertTrue(real_values_are_equal(feature['real_value'], 1.41, 3))

    def _test_skip_some(self, input_layer_name, output_layer, input_layer_path=None):
        if input_layer_path is None:
            # Note that when input and output are in the same DB, input_layer_path should be passed as arg
            # so that no other temp file is generated.
            input_layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(input_layer_path, input_layer_name)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, output_layer])

        # First, let's have some records to be able to test the skip mode
        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # Let's modify values in the input layer to be able to check that
        # these new values are never transferred to the output layer
        input_layer.dataProvider().changeAttributeValues({1: {3: 30}})  # real_value --> 30

        # Also create a new feature that won't be skipped but appended
        new_feature = QgsFeature()
        new_feature.setAttributes([5, 'ABC', 1, 2.0])
        input_layer.dataProvider().addFeatures([new_feature])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 3)
        self.assertEqual(res[APPENDED_COUNT], 1)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 2)

        feature = next(output_layer.getFeatures('"name"=\'abc\''))
        self.assertTrue(real_values_are_equal(feature['real_value'], 3.1416, 5))

        feature = next(output_layer.getFeatures('"name"=\'ABC\''))
        self.assertEqual(feature['real_value'], 2.0)

    def _test_skip_none(self, input_layer_name, output_layer, input_layer_path=None):
        if input_layer_path is None:
            # Note that when input and output are in the same DB, input_layer_path should be passed as arg
            # so that no other temp file is generated.
            input_layer_path = get_test_file_copy_path('insert_features_to_layer_test.gpkg')

        input_layer_path = "{}|layername={}".format(input_layer_path, input_layer_name)
        input_layer = QgsVectorLayer(input_layer_path, 'layer name', 'ogr')
        self.assertTrue(input_layer.isValid())

        QgsProject.instance().addMapLayers([input_layer, output_layer])

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': None,
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': None,
                              'ACTION_ON_DUPLICATE': 0})  # No action

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 2)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # These are None because ACTION_ON_DUPLICATE is None
        self.assertIsNone(res[SKIPPED_COUNT])

        # Let's modify values in the input layer to make them unmatchable
        # and thus, be able to test a skip none scenario (i.e., no duplicates found)
        input_layer.dataProvider().changeAttributeValues({1: {1: 'abcd'}})  # text_value --> abcd
        input_layer.dataProvider().changeAttributeValues({2: {1: 'defg'}})  # text_value --> defg

        res = processing.run("etl_load:appendfeaturestolayer",
                             {'SOURCE_LAYER': input_layer,
                              'SOURCE_FIELD': 'name',
                              'TARGET_LAYER': output_layer,
                              'TARGET_FIELD': 'name',
                              'ACTION_ON_DUPLICATE': 1})  # Skip

        self.assertEqual(res['TARGET_LAYER'].featureCount(), 4)
        self.assertEqual(res[APPENDED_COUNT], 2)
        self.assertIsNone(res[UPDATED_FEATURE_COUNT])  # This is None because ACTION_ON_DUPLICATE is Skip
        self.assertEqual(res[SKIPPED_COUNT], 0)  # Input features not found in target
