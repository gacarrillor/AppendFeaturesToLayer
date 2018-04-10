# Append Features to Layer

Processing plugin-based provider for QGIS 3 that adds an algorithm for appending features to a vector layer.

Such algorithm acts as the 'Load' in an ETL (Extract, Transform and Load) operation, allowing you to store data into your target layer instead of into temporary layers.

This algorithm is based on the `Paste` tool that QGIS offers in its main user interface, enabling you to use it in your Processing workflows.

Think about `Append Features to Layer` as a Copy & Paste algorithm, which extracts features from a source vector layer and pastes them into a target vector layer.



Where to find the algorithm
---------------------------

Once installed and activated, this plugin adds a new provider (`ETL_LOAD`) to QGIS Processing.
You can find the `Append Features to Layer` algorithm in the Processing Toolbox, under `ETL_LOAD -> Vector table -> Append features to layer`.

![New algorithm provider][1]

Additionally, as an example, this plugin also installs a Processing model that uses `Refactor Fields` and `Append features to layer` algorithms. You can find the model under `Models --> ETL_LOAD --> ETL-basic-model`. This model deals with the temporary/intermediate vector layer that `Refactor Fields` creates and allows you to focus on your real target layer instead. Of course, your target layer should be editable.

![ETL-basic-model][2]

![ETL-basic-model_dialog][3]

[1]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/newly_added_algorithm_and_model.png
[2]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/model_etl_load.png
[3]: http://downloads.tuxfamily.org/tuxgis/geoblogs/AppendFeaturesToLayer/etl_basic_model.png
