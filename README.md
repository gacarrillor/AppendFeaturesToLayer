![Unit tests](https://github.com/gacarrillor/AppendFeaturesToLayer/actions/workflows/main.yml/badge.svg)
[![Release](https://img.shields.io/github/v/release/gacarrillor/AppendFeaturesToLayer.svg)](https://github.com/gacarrillor/AppendFeaturesToLayer/releases)

# Append Features to Layer


QGIS v3 plugin that adds a new Processing algorithm to append/update features from a `source` vector layer to an existing `target` vector layer.

**License**: This plugin is distributed under the [GNU GPL v3 license](https://github.com/gacarrillor/AppendFeaturesToLayer/blob/master/AppendFeaturesToLayer/LICENSE).

➡️  [Use cases](#%EF%B8%8F-use-cases)<br>
🛠️  [How does it work](#%EF%B8%8F-how-does-it-work)<br>
🔎  [Where to find the algorithm](#-where-to-find-the-algorithm)<br>
📝  [Examples](#-examples)<br>
🐍  [Using Append Features to Layer in standalone PyQGIS scripts](#-using-append-features-to-layer-in-standalone-pyqgis-scripts)<br>
⚙️  [Using Append Features to Layer via QGIS Process](#%EF%B8%8F-using-append-features-to-layer-via-qgis-process)<br>
💻  [Running Unit Tests Locally](#-running-unit-tests-locally)

-----------

### ➡️ Use cases

 1. **Copy & Paste features**:

    Think about `Append Features to Layer` as a Copy & Paste algorithm, which extracts features from a `source` vector layer and pastes them into an existing `target` vector layer.

    In fact, the algorithm is based on the `Paste` tool that QGIS offers in its main user interface, enabling you to use it in your Processing workflows. 

 2. **ETL (Extract, Transform and Load)**: (See [example](#-examples) number 2)
    
    The `Append Features to Layer` algorithm acts as the 'Load' in an ETL operation. If you need to 'Transform' your features before using the 'Load', QGIS offers the `Refactor fields` algorithm. 
    
    Using both algorithms in a model, you can create complex ETL processes to migrate entire data sets from a data structure into another. Fortunately, you can find such a model after installing this plugin!

 3. **Send the output of a Processing algorithm to an existing layer**:

    Unlike conventional QGIS Processing algorithms (except by *in-place* ones), `Append Features to Layer` allows you to store data into an existing `target` layer instead of into temporary layers. 
    
    For instance, if you need to send the buffers of a point layer into an existing polygon layer, you can chain the Buffer and `Append Features to Layer` algorithms in the Processing modeler, so that the output from the buffer gets copied into your polygon layer.    

 4. **Update existing features in an existing (`target`) layer based on a `source` layer**.

    The `Append Features to Layer` algorithm can search for duplicates while copying features from `source` to `target` layers. If duplicates are found, the algorithm can **update** the existing feature's geometry/attributes based on the source feature, instead of appending it. In other words, the algorithm performs an **Upsert** (Update or Insert a feature). You can find more details in the next section of this document.

 5. **Update existing geometries in a (`target`) layer based on geometries from a `source` layer**. 🆕

    The `Append Features to Layer` algorithm can search for duplicates while copying features from `source` to `target` layers. If duplicates are found, the algorithm can **update** the existing feature's geometry (leaving all feature attributes intact) based on the source feature's geometry, instead of appending it. In other words, the algorithm performs an **Upsert** (Update a geometry or Insert a feature). You can find more details in the next section of this document.


### 🛠️ How does it work

**Fields and geometries**

Field mapping between `source` and `target` layers is handled automatically. Fields that are in both layers are copied. Fields that are only found in `source` are not copied to `target` layer.

Geometry conversion is done on the fly, if required by the `target` layer. For instance, single-part geometries are converted to multi-part if `target` layer handles multi-geometries; polygons are converted to lines if `target` layer stores lines; among others.

**How the algorithm deals with duplicates**

This algorithm allows you to choose a field in `source` and `target` layers to compare and detect duplicates. It has 4 modes of operation:

  1) APPEND new feature, regardless of duplicates.
  2) SKIP new feature if duplicate is found.
  3) UPDATE EXISTING FEATURE in `target` layer with attributes (including geometry) from the feature in the `source` layer.
  4) ONLY UPDATE EXISTING FEATURE's GEOMETRY in `target` layer (leaving its attributes intact) based on the feature's geometry in the `source` layer.

**Note on Primary Keys**

The algorithm deals with target layer's Primary Keys in this way:

|           PRIMARY KEY           |                                                    APPEND mode                                                     |                UPDATE mode                 |
|:-------------------------------:|:------------------------------------------------------------------------------------------------------------------:|:------------------------------------------:|
| Automatic PK<br/>(e.g., serial) |               It lets the provider (e.g., PostgreSQL, GeoPackage, etc.) fill the value automatically               | It doesn't modify the value already stored |
|        Non-automatic PK         | You need to provide a value for the PK in the source layer, because such value wil be set in the target layer's PK | It doesn't modify the value already stored |

**Note on geometry updates**

Mode UPDATE EXISTING FEATURE:
  + If target layer has geometries but input layer does not, then only attributes will be updated when a duplicate feature is found, i.e., the geometry in target layer will remain untouched.


### 🔎 Where to find the algorithm

Once installed and activated, this plugin adds a new provider (`ETL_LOAD`) to QGIS Processing.
You can find the `Append Features to Layer` algorithm in the Processing Toolbox, under `ETL_LOAD -> Vector table -> Append features to layer`.

![image](https://github.com/gacarrillor/AppendFeaturesToLayer/assets/652785/1d9cda0b-eccd-4c12-8ed3-511e47c576fc)


### 📝 Examples

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

### 🐍 Using Append Features to Layer in standalone PyQGIS scripts

Chances are you'd like to run this plugin from a PyQGIS script that works out of a QGIS GUI session. For that, take "[Using QGIS Processing algorithms from PyQGIS standalone scripts](https://gis.stackexchange.com/questions/279874/using-qgis-processing-algorithms-from-pyqgis-standalone-scripts-outside-of-gui)" into account, as well as the following code snippet.

```python
# Add the path to QGIS plugins so that you can import AppendFeaturesToLayer
# See paths in https://gis.stackexchange.com/questions/274311/274312#274312
sys.path.append(path_to_qgis_plugins)

from AppendFeaturesToLayer.processing.etl_load_provider import ETLLoadAlgorithmProvider

# Register the processing provider
provider = ETLLoadAlgorithmProvider()
qgis.core.QgsApplication.processingRegistry().addProvider(provider)

# Finally, enjoy!
result = processing.run("etl_load:appendfeaturestolayer",
                        {'SOURCE_LAYER': source_layer,
                         'SOURCE_FIELD': '',
                         'TARGET_LAYER': target_layer,
                         'TARGET_FIELD': '',
                         'ACTION_ON_DUPLICATE': 0})  # NO_ACTION: 0
                                                     # SKIP_FEATURE: 1
                                                     # UPDATE_EXISTING_FEATURE: 2
                                                     # ONLY_UPDATE_EXISTING_FEATURES_GEOMETRY: 3
```

The algorithm outputs are:

 + `TARGET_LAYER`
 + `APPENDED_COUNT`
 + `SKIPPED_COUNT`
 + `UPDATED_FEATURE_COUNT`
 + `UPDATED_ONLY_GEOMETRY_COUNT` :new: 


### ⚙️ Using Append Features to Layer via QGIS Process

If you'd like to run the plugin without GUI, but don't want to deal with PyQGIS scripts, you can use QGIS Process. You run QGIS Process from the operating system's terminal, in this way:

```$ qgis_process run "etl_load:appendfeaturestolayer" -- SOURCE_LAYER=/tmp/source.shp TARGET_LAYER=/tmp/target.shp ACTION_ON_DUPLICATE=0```

Where `NO_ACTION`: 0, `SKIP_FEATURE`: 1, `UPDATE_EXISTING_FEATURE`: 2, `ONLY_UPDATE_EXISTING_FEATURES_GEOMETRY`: 3

Make sure the plugin can be found in your QGIS plugins folder, that is, that you have installed the plugin in your QGIS.


### 💻 Running Unit Tests Locally

First, you need to set 2 environment variables:

    export GITHUB_WORKSPACE=/path/to/AppendFeaturesToLayer/
    export QGIS_TEST_VERSION="3.40.15-noble"

After that, you could run unit tests locally with this command:

    docker compose -f .docker/docker-compose.yml run -e PYTHONPATH=/usr/share/qgis/python/plugins --rm qgis

You could rebuild the Docker image in this way:

    docker compose -f .docker/docker-compose.yml down --rmi local && docker-compose -f .docker/docker-compose.yml build
