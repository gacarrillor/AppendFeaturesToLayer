[![License](https://img.shields.io/github/license/gacarrillor/AppendFeaturesToLayer.svg)](https://tldrlegal.com/license/gnu-general-public-license-v3-%28gpl-3%29)
[![Build Status](https://api.travis-ci.org/gacarrillor/AppendFeaturesToLayer.svg?branch=master)](https://travis-ci.org/gacarrillor/AppendFeaturesToLayer)


# Append Features to Layer


QGIS v3 plugin that adds a new Processing algorithm to append/update features from a `source` vector layer to an existing `target` vector layer.


  [Use cases](#use-cases)<br>
  [How does it work](#how-does-it-work)<br>
  [Where to find the algorithm](#where-to-find-the-algorithm)<br>
  [Examples](#examples)<br>
  [Running Unit Tests Locally](#running-unit-tests-locally)


### Use cases

 1. **Copy & Paste features**:

    Think about `Append Features to Layer` as a Copy & Paste algorithm, which extracts features from a `source` vector layer and pastes them into an existing `target` vector layer.

    In fact, the algorithm is based on the `Paste` tool that QGIS offers in its main user interface, enabling you to use it in your Processing workflows. 

 2. **ETL (Extract, Transform and Load)**: (See [example](#examples) number 2)
    
    The `Append Features to Layer` algorithm acts as the 'Load' in an ETL operation. If you need to 'Transform' your features before using the 'Load', QGIS offers the `Refactor fields` algorithm. 
    
    Using both algorithms in a model, you can create complex ETL processes to migrate entire data sets from a data structure into another. Fortunately, you can find such a model after installing this plugin!

 3. **Send the output of a Processing algorithm to an existing layer**:

    Unlike conventional QGIS Processing algorithms (except by *in-place* ones), `Append Features to Layer` allows you to store data into an existing `target` layer instead of into temporary layers. 
    
    For instance, if you need to send the buffers of a point layer into an existing polygon layer, you can chain the Buffer and `Append Features to Layer` algorithms in the Processing modeler, so that the output from the buffer gets copied into your polygon layer.    

 4. **Update existing features in an existing (`target`) layer based on a `source` layer**.

    The `Append Features to Layer` algorithm can search for duplicates while copying features from `source` to `target` layers. If duplicates are found, the algorithm can **update** the existing feature's geometry/attributes based on the new feature, instead of appending it. You can find more details below.


### How does it work?

**Fields and geometries**

Field mapping between `source` and `target` layers is handled automatically. Fields that are in both layers are copied. Fields that are only found in `source` are not copied to `target` layer.

Geometry conversion is done on the fly, if required by the `target` layer. For instance, single-part geometries are converted to multi-part if `target` layer handles multi-geometries; polygons are converted to lines if `target` layer stores lines; among others.

**How the algorithm deals with duplicates**

This algorithm allows you to choose a field in `source` and `target` layers to compare and detect duplicates. It has 3 modes of operation: 

  1) APPEND new feature, regardless of duplicates.
  2) SKIP new feature if duplicate is found.
  3) UPDATE the feature in `target` layer, based on attributes from the feature in the `source` layer.


### Where to find the algorithm


Once installed and activated, this plugin adds a new provider (`ETL_LOAD`) to QGIS Processing.
You can find the `Append Features to Layer` algorithm in the Processing Toolbox, under `ETL_LOAD -> Vector table -> Append features to layer`.

![Algorithm][1]

### Examples

1. **Copy & Paste features**

2. **ETL (Extract, Transform and Load)**: 

   This plugin also installs 2 Processing models that chain `Refactor Fields` and `Append features to layer` algorithms. You can find the models under `Models --> ETL_LOAD`. 
   
   The models allow you to 
   
   i) Transform and Load (APPEND) all features from the `source` layer, or
   
      ![ETL-basic-model-append][2]

      ![ETL-basic-model_dialog_append][3]    
   
   ii) Transform and Load (UPDATE) all features from the `source`, updating those features that are duplicate.

      ![ETL-basic-model-update][4]

      ![ETL-basic-model_dialog_update][5]


[1]: https://imgur.com/0xtH0kV.png
[2]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/append_01.png
[3]: https://imgur.com/032tTlB.png
[4]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/imgs/update_01.png
[5]: https://imgur.com/6P8iSuv.png

### Running Unit Tests Locally

`me@my-pc:/path/to/AppendFeaturesToLayer$ docker build --build-arg QGIS_TEST_VERSION=release-3_16 -t append .; docker run --rm append bash /usr/src/run-docker-tests.sh`
