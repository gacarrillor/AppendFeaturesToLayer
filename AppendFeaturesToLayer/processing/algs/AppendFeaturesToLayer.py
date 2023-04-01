"""
/***************************************************************************
                           Append Features to Layer
                             --------------------
        begin                : 2018-04-09
        git sha              : :%H$
        copyright            : (C) 2018 by Germán Carrillo (BSF Swissphoto)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import (QVariant,
                              QCoreApplication)

from qgis.core import (edit,
                       QgsEditError,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsProject,
                       QgsVectorLayerUtils,
                       QgsVectorDataProvider,
                       QgsProcessingOutputNumber,
                       QgsFeatureRequest)


class AppendFeaturesToLayer(QgsProcessingAlgorithm):

    INPUT = 'SOURCE_LAYER'
    INPUT_FIELD = 'SOURCE_FIELD'
    OUTPUT = 'TARGET_LAYER'
    OUTPUT_FIELD = 'TARGET_FIELD'
    ACTION_ON_DUPLICATE = 'ACTION_ON_DUPLICATE'

    APPENDED_COUNT = 'APPENDED_COUNT'
    UPDATED_COUNT = 'UPDATED_COUNT'
    SKIPPED_COUNT = 'SKIPPED_COUNT'

    NO_ACTION_TEXT = "Just APPEND all features, no matter of duplicates"
    SKIP_FEATURE_TEXT = 'If duplicate is found, SKIP feature'
    UPDATE_EXISTING_FEATURE_TEXT = 'If duplicate is found, UPDATE existing feature'
    NO_ACTION = 0
    SKIP_FEATURE = 1
    UPDATE_EXISTING_FEATURE = 2

    def createInstance(self):
        return type(self)()

    def group(self):
        return QCoreApplication.translate("AppendFeaturesToLayer", 'Vector table')

    def groupId(self):
        return 'vectortable'

    def tags(self):
        return (QCoreApplication.translate("AppendFeaturesToLayer", 'append,copy,insert,update,features,paste,load,etl,load data')).split(',')

    def __init__(self):
        super().__init__()

    def shortHelpString(self):
        return QCoreApplication.translate("AppendFeaturesToLayer", "This algorithm copies features from a source layer into a target layer.\n\n"
                                          "Field mapping is handled automatically. Fields that are in both source and target layers are copied. Fields that are only found in source are not copied to target layer.\n\n"
                                          "Geometry conversion is done automatically, if required by the target layer. For instance, single-part geometries are converted to multi-part if target layer handles multi-geometries; polygons are converted to lines if target layer stores lines; among others.\n\n"
                                          "This algorithm allows you to choose a field in source and target layers to compare and detect duplicates. It has 3 modes of operation: 1) APPEND feature, regardless of duplicates; 2) SKIP feature if duplicate is found; or 3) UPDATE the feature in target layer with attributes (including geometry) from the feature in the source layer.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,
                                                              QCoreApplication.translate("AppendFeaturesToLayer", 'Source layer'),
                                                              [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD,
                                                      QCoreApplication.translate("AppendFeaturesToLayer", 'Source field to compare'),
                                                      None,
                                                      self.INPUT,
                                                      optional=True))
        self.addParameter(QgsProcessingParameterVectorLayer(self.OUTPUT,
                                                              QCoreApplication.translate("AppendFeaturesToLayer", 'Target layer'),
                                                              [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterField(self.OUTPUT_FIELD,
                                                      QCoreApplication.translate("AppendFeaturesToLayer", 'Target field to compare'),
                                                      None,
                                                      self.OUTPUT,
                                                      optional=True))
        self.addParameter(QgsProcessingParameterEnum(self.ACTION_ON_DUPLICATE,
                                                     QCoreApplication.translate("AppendFeaturesToLayer", 'Action for duplicate features'),
                                                     [self.NO_ACTION_TEXT, self.SKIP_FEATURE_TEXT, self.UPDATE_EXISTING_FEATURE_TEXT],
                                                     False,
                                                     self.NO_ACTION_TEXT,
                                                     optional=False))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT,
                                                      QCoreApplication.translate("AppendFeaturesToLayer",
                                                                                 "Target layer to paste new features")))
        self.addOutput(QgsProcessingOutputNumber(self.APPENDED_COUNT,
                                                 QCoreApplication.translate("AppendFeaturesToLayer",
                                                                            "Number of features appended")))
        self.addOutput(QgsProcessingOutputNumber(self.UPDATED_COUNT,
                                                 QCoreApplication.translate("AppendFeaturesToLayer",
                                                                            "Number of features updated")))
        self.addOutput(QgsProcessingOutputNumber(self.SKIPPED_COUNT,
                                                 QCoreApplication.translate("AppendFeaturesToLayer",
                                                                            "Number of features skipped")))

    def name(self):
        return 'appendfeaturestolayer'

    def displayName(self):
        return QCoreApplication.translate("AppendFeaturesToLayer", 'Append features to layer')

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        source_fields_parameter = self.parameterAsFields(parameters, self.INPUT_FIELD, context)
        target = self.parameterAsVectorLayer(parameters, self.OUTPUT, context)
        target_fields_parameter = self.parameterAsFields(parameters, self.OUTPUT_FIELD, context)
        action_on_duplicate = self.parameterAsEnum(parameters, self.ACTION_ON_DUPLICATE, context)

        results = {self.OUTPUT: None,
                   self.APPENDED_COUNT: None,
                   self.UPDATED_COUNT: None,
                   self.SKIPPED_COUNT: None}

        target_value_dict = dict()
        source_field_unique_values = ''
        target_field_unique_values = ''
        source_field_type = None
        target_field_type = None

        if source_fields_parameter:
            source_field_unique_values = source_fields_parameter[0]
            if source.fields().indexOf(source_field_unique_values) == -1:
                feedback.reportError(
                    "\nWARNING: '{field}' field not found in source layer! If you're using an ETL model, the '{field}' field must be included in the mapping.".format(field=source_field_unique_values))
                return results

            source_field_type = source.fields().field(source_field_unique_values).type()

        if target_fields_parameter:
            target_field_unique_values = target_fields_parameter[0]
            if target.fields().indexOf(target_field_unique_values) == -1:
                feedback.reportError(
                    "\nWARNING: '{field}' field not found in target layer! If you're using an ETL model, the '{field}' field must be included in the mapping.".format(field=target_field_unique_values))
                return results

            target_field_type = target.fields().field(target_field_unique_values).type()

        if source_field_type != target_field_type:
            feedback.pushInfo("\nWARNING: Source and target fields to compare have different field types.")

        if source_field_unique_values and target_field_unique_values and action_on_duplicate == self.NO_ACTION:
            feedback.reportError("\nWARNING: Since you have chosen source and target fields to compare, you need to choose a valid action to apply on duplicate features before running this algorithm.")
            return results

        if action_on_duplicate != self.NO_ACTION and not (source_field_unique_values and target_field_unique_values):
            feedback.reportError("\nWARNING: Since you have chosen an action on duplicate features, you need to choose both source and target fields for comparing values before running this algorithm.")
            return results

        caps = target.dataProvider().capabilities()
        if not(caps & QgsVectorDataProvider.AddFeatures):
            feedback.reportError("\nWARNING: The target layer does not support appending features to it! Choose another target layer.")
            return results

        if action_on_duplicate == self.UPDATE_EXISTING_FEATURE and not(caps & QgsVectorDataProvider.ChangeAttributeValues and caps & QgsVectorDataProvider.ChangeGeometries):
            feedback.reportError("\nWARNING: The target layer does not support updating its features! Choose another action for duplicate features or choose another target layer.")
            return results

        editable_before = False
        if target.isEditable():
            editable_before = True
            feedback.reportError("\nWARNING: You need to close the edit session on layer '{}' before running this algorithm.".format(
                target.name()
            ))
            return results

        # Define a mapping between source and target layer
        mapping = dict()
        for target_idx in target.fields().allAttributesList():
            if target_idx in target.primaryKeyAttributes():
                continue  # We won't be able to update PKs, so skip it

            target_field = target.fields().field(target_idx)

            if target.dataProvider().storageType() == 'GPKG' and target_field.name() == 'fid':
                continue  # We won't be able to update a GPKG FID, so skip it.

            source_idx = source.fields().indexOf(target_field.name())
            if source_idx != -1:
                mapping[target_idx] = source_idx

        # Build dict of target field values so that we can search easily later {value1: [id1, id2], ...}
        if target_field_unique_values:
            for f in target.getFeatures():
                if f[target_field_unique_values] in target_value_dict:
                    target_value_dict[f[target_field_unique_values]].append(int(f.id()))
                else:
                    target_value_dict[f[target_field_unique_values]] = [int(f.id())]

        # Prepare features for the Copy and Paste
        results[self.APPENDED_COUNT] = 0
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        destType = target.geometryType()
        destIsMulti = QgsWkbTypes.isMultiType(target.wkbType())
        new_features = list()
        updated_features = dict()
        updated_geometries = dict()
        updated_features_count = 0
        updated_geometries_count = 0
        skipped_features_count = 0  # To properly count features that were skipped
        duplicate_features_set = set()  # To properly count features that were updated
        for current, in_feature in enumerate(features):
            if feedback.isCanceled():
                break

            target_feature_exists = False
            duplicate_target_value = None

            # If skip is the action, skip as soon as possible
            if source_field_unique_values:
                duplicate_target, duplicate_target_value = self.find_duplicate_value(
                    in_feature[source_field_unique_values],
                    source_field_type,
                    target_value_dict,
                    target_field_type)
                if duplicate_target:
                    if action_on_duplicate == self.SKIP_FEATURE:
                        request = QgsFeatureRequest(target_value_dict[duplicate_target_value])  # Get target feature ids
                        request.setFlags(QgsFeatureRequest.NoGeometry)
                        request.setSubsetOfAttributes([])  # Note: this adds a new flag
                        skipped_features_count += len([f for f in target.getFeatures(request)])
                        continue

                    target_feature_exists = True

            attrs = {target_idx: in_feature[source_idx] for target_idx, source_idx in mapping.items()}

            geom = QgsGeometry()

            if QgsWkbTypes.geometryType(
                    source.wkbType()) != QgsWkbTypes.NullGeometry and in_feature.hasGeometry() and target.isSpatial():
                # Convert geometry to match destination layer
                # Adapted from QGIS qgisapp.cpp, pasteFromClipboard()
                geom = in_feature.geometry()

                if not geom.isNull():
                    if destType != QgsWkbTypes.UnknownGeometry:
                        newGeometry = geom.convertToType(destType, destIsMulti)

                        if newGeometry.isNull():
                            continue  # Couldn't convert
                        geom = newGeometry

                    # Avoid intersection if enabled in digitize settings
                    geom.avoidIntersections(QgsProject.instance().avoidIntersectionsLayers())

            if target_feature_exists and action_on_duplicate == self.UPDATE_EXISTING_FEATURE:
                for t_f in target.getFeatures(target_value_dict[duplicate_target_value]):
                    duplicate_features_set.add(t_f.id())
                    updated_features[t_f.id()] = attrs
                    if QgsWkbTypes.geometryType(source.wkbType()) != QgsWkbTypes.NullGeometry and target.isSpatial():
                        # Only overwrite geometry if both source and target layers are spatial
                        updated_geometries[t_f.id()] = geom
            else:  # Append
                new_feature = QgsVectorLayerUtils().createFeature(target, geom, attrs)
                new_features.append(new_feature)

            feedback.setProgress(int(current * total))

        # Do the Copy and Paste
        res_add_features = False
        try:
            with edit(target):
                target.beginEditCommand("Appending/Updating features...")

                if updated_features:
                    for k, v in updated_features.items():
                        if target.changeAttributeValues(k, v):
                            updated_features_count += 1
                        else:
                            feedback.reportError("\nERROR: Target feature (id={}) couldn't be updated to the following attributes: {}.".format(k, v))

                if updated_geometries:
                    for k,v in updated_geometries.items():
                        if target.changeGeometry(k, v):
                            updated_geometries_count += 1
                        else:
                            feedback.reportError("\nERROR: Target feature's geometry (id={}) couldn't be updated.".format(k))

                if new_features:
                    res_add_features = target.addFeatures(new_features)

                target.endEditCommand()
        except QgsEditError as e:
            if not editable_before:
                # Let's close the edit session to prepare for a next run
                target.rollBack()

            feedback.reportError("\nERROR: No features could be appended/updated to/in '{}', because of the following error:\n{}\n".format(
                target.name(),
                repr(e)
            ))
            return results

        if action_on_duplicate == self.SKIP_FEATURE:
            feedback.pushInfo("\nSKIPPED FEATURES: {} duplicate features were skipped while copying features to '{}'!".format(
                skipped_features_count,
                target.name()
            ))
            results[self.SKIPPED_COUNT] = skipped_features_count

        if action_on_duplicate == self.UPDATE_EXISTING_FEATURE:
            feedback.pushInfo("\nUPDATED FEATURES: {} out of {} duplicate features were updated while copying features to '{}'!".format(
                updated_features_count,
                len(duplicate_features_set),
                target.name()
            ))
            results[self.UPDATED_COUNT] = updated_features_count

        if not new_features:
            feedback.pushInfo("\nFINISHED WITHOUT APPENDED FEATURES: There were no features to append to '{}'.".format(
                target.name() if target.name() else target.source()
            ))
        else:
            if res_add_features:
                feedback.pushInfo("\nAPPENDED FEATURES: {} out of {} features from input layer were successfully appended to '{}'!".format(
                    len(new_features),
                    source.featureCount(),
                    target.name()
                ))
                results[self.APPENDED_COUNT] = len(new_features)
            else: # TODO do we really need this else message below?
                feedback.reportError("\nERROR: The {} features from input layer could not be appended to '{}'. Sometimes this might be due to NOT NULL constraints that are not met.".format(
                    source.featureCount(),
                    target.name()
                ))

        results[self.OUTPUT] = target
        return results

    def find_duplicate_value(self, source_value, source_field_type, target_value_dict, target_field_type):
        """
        Check if source_value is in target layer. First, as is, and if necessary as a converted value.

        :param source_value: single value from the source layer
        :param source_field_type: QVariant.Type
        :param target_value_dict: dict of unique values in the target layer. We only use keys in this function.
        :param target_field_type: QVariant.Type
        :return: Whether the source_value is duplicated in the target layer and, if so, also the target value
        """
        # Direct comparison
        if source_field_type == target_field_type:
            if source_value in target_value_dict:
                return True, source_value
            else:
                return False, None

        # We first need to convert types before comparing...
        qvariant_value = QVariant(source_value)
        res_can_convert = qvariant_value.canConvert(target_field_type)
        if res_can_convert:
            res_convert = qvariant_value.convert(target_field_type)
            if res_convert:
                if qvariant_value.value() in target_value_dict:
                    return True, qvariant_value.value()

        return False, None
