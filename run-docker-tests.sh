#!/usr/bin/env bash
pushd /usr/src/
xvfb-run nose2-3
#xvfb-run nose2-3 tests.test_pg_table_pg_table
#xvfb-run nose2-3 tests.test_table_table
#xvfb-run nose2-3 tests.test_source_simple_polygons
#xvfb-run nose2-3 tests.test_spatial_and_non_spatial
popd
