[![License](https://img.shields.io/github/license/gacarrillor/AppendFeaturesToLayer.svg)](https://tldrlegal.com/license/gnu-general-public-license-v3-%28gpl-3%29)
[![Build Status](https://api.travis-ci.org/gacarrillor/AppendFeaturesToLayer.svg?branch=master)](https://travis-ci.org/gacarrillor/AppendFeaturesToLayer)


# Append Features to Layer

Processing plugin-based provider for QGIS 3 that adds an algorithm for appending features to a vector layer.

Such algorithm acts as the 'Load' in an ETL (Extract, Transform and Load) operation, allowing you to store data into your target layer instead of into temporary layers.

This algorithm is based on the `Paste` tool that QGIS offers in its main user interface, enabling you to use it in your Processing workflows.

Think about `Append Features to Layer` as a Copy & Paste algorithm, which extracts features from a source vector layer and pastes them into a target vector layer.

**Fields and geometries**

Field mapping is handled automatically. Fields that are in both source and target layers are copied. Fields that are only found in source are not copied to target layer.

Geometry conversion is done automatically, if required by the target layer. For instance, single-part geometries are converted to multi-part if target layer handles multi-geometries; polygons are converted to lines if target layer stores lines; among others.

**How the algorithm deals with duplicates**

This algorithm allows you to choose a field in source and target layers to compare and detect duplicates. It has 3 modes of operation: 

  1) APPEND feature, regardless of duplicates.
  2) SKIP feature if duplicate is found.
  3) UPDATE the feature in target layer with attributes from the feature in the source layer.


Where to find the algorithm
---------------------------

Once installed and activated, this plugin adds a new provider (`ETL_LOAD`) to QGIS Processing.
You can find the `Append Features to Layer` algorithm in the Processing Toolbox, under `ETL_LOAD -> Vector table -> Append features to layer`.

![New algorithm provider][1]

Additionally, as an example, this plugin also installs 2 Processing models that use `Refactor Fields` and `Append features to layer` algorithms. You can find the models under `Models --> ETL_LOAD`. The algorithms allow you to 1) APPEND all features from the source layer or 2) UPDATE duplicate features and append the rest.

![ETL-basic-model-append][2]

![ETL-basic-model_dialog_append][3]

![ETL-basic-model-update][4]

![ETL-basic-model_dialog_update][5]


[1]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/append.png
[2]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/append_01.png
[3]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/append_02.png
[4]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/update_01.png
[5]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/update_02.png

Running Unit Tests Locally
----------------------

`me@my-pc:/path/to/AppendFeaturesToLayer$ docker build --build-arg QGIS_TEST_VERSION=latest -t append .; docker run --rm append bash /usr/src/run-docker-tests.sh`
