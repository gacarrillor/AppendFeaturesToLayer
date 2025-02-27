#!/usr/bin/env bash
set -e

printf "Wait a moment while loading the PG database."
for i in {1..15}
do
  if PGPASSWORD='pass1' psql -h postgres -U user1 -p 5432 -l &> /dev/null; then
    break
  fi
  printf "\nAttempt $i..."
  sleep 2
done
printf "\nPostgreSQL ready!\n"

pushd /usr/src/
xvfb-run pytest
#xvfb-run nose2-3 tests.test_pk
#xvfb-run nose2-3 tests.test_table_table
#xvfb-run nose2-3 tests.test_pg_table_pg_table
#xvfb-run nose2-3 tests.test_table_table
#xvfb-run nose2-3 tests.test_source_simple_polygons
#xvfb-run nose2-3 tests.test_spatial_and_non_spatial
popd
