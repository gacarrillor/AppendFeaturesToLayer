#!/usr/bin/env bash
pushd /usr/src/
xvfb-run nose2-3
#xvfb-run nose2-3 tests.test_pg_table_pg_table
popd
