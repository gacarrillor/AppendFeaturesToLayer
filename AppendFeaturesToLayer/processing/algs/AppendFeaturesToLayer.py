#-*- coding: utf-8 -*-
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
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QCoreApplication

from qgis.core import (
                       edit,
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
                       QgsVectorLayerUtils
                       )

class AppendFeaturesToLayer(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    INPUT_FIELD = 'INPUT_FIELD'
    OUTPUT = 'OUTPUT'
    OUTPUT_FIELD = 'OUTPUT_FIELD'
    ACTION_ON_DUPLICATE = 'ACTION_ON_DUPLICATE'

    SKIP_FEATURE_TEXT = 'Skip feature'
    UPDATE_EXISTING_FEATURE_TEXT = 'Update existing feature'
    SKIP_FEATURE = 1
    UPDATE_EXISTING_FEATURE = 2

    def createInstance(self):
        return type(self)()

    def group(self):
        return QCoreApplication.translate("AppendFeaturesToLayer", 'Vector table')

    def groupId(self):
        return 'vectortable'

    def tags(self):
        return (QCoreApplication.translate("AppendFeaturesToLayer", 'append,copy,insert,update,features,paste,load,etl')).split(',')

    def __init__(self):
        super().__init__()

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
                                                      QCoreApplication.translate("AppendFeaturesToLayer", 'Action when value exists in target'),
                                                      [None, self.SKIP_FEATURE_TEXT, self.UPDATE_EXISTING_FEATURE_TEXT],
                                                      False,
                                                      QVariant(),
                                                      optional=True))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT,
                                                        QCoreApplication.translate("AppendFeaturesToLayer", 'Target layer to paste new features')))

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

        target_value_dict = dict()
        source_field_unique_values = ''
        target_field_unique_values = ''

        if source_fields_parameter:
            source_field_unique_values = source_fields_parameter[0]

        if target_fields_parameter:
            target_field_unique_values = target_fields_parameter[0]

        if source_field_unique_values and target_field_unique_values and not action_on_duplicate:
            feedback.reportError("\nWARNING: Since you have chosen source and target fields to compare, you need to choose an action to apply on duplicate features before running this algorithm.")
            return {self.OUTPUT: None}

        if action_on_duplicate and not source_field_unique_values and not target_field_unique_values:
            feedback.reportError("\nWARNING: Since you have chosen an action on duplicate features, you need to choose both source and target fields for comparing values before running this algorithm.")
            return {self.OUTPUT: None}

        editable_before = False
        if target.isEditable():
            editable_before = True
            feedback.reportError("\nWARNING: You need to close the edit session on layer '{}' before running this algorithm.".format(
                target.name()
            ))
            return {self.OUTPUT: None}

        # Define a mapping between source and target layer
        mapping = dict()
        for target_idx in target.fields().allAttributesList():
            target_field = target.fields().field(target_idx)
            source_idx = source.fields().indexOf(target_field.name())
            if source_idx != -1:
                mapping[target_idx] = source_idx

        # Build dict of target field values so that we can search easily later
        if target_field_unique_values:
            for f in target.getFeatures():
                if f[target_field_unique_values] in target_value_dict:
                    target_value_dict[f[target_field_unique_values]].append(int(f.id()))
                else:
                    target_value_dict[f[target_field_unique_values]] = [int(f.id())]

        # Prepare features for the Copy and Paste
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        destType = target.geometryType()
        destIsMulti = QgsWkbTypes.isMultiType(target.wkbType())
        new_features = list()
        updated_features = dict()
        updated_geometries = dict()
        updated_features_count = 0
        updated_geometries_count = 0
        skipped_features_count = 0
        duplicate_features_count = 0
        for current, in_feature in enumerate(features):
            if feedback.isCanceled():
                break

            target_feature_exists = False

            if source_field_unique_values:
                if in_feature[source_field_unique_values] in target_value_dict:
                    duplicate_features_count += 1
                    if action_on_duplicate == self.SKIP_FEATURE:
                        skipped_features_count += 1
                        continue
                    else:
                        target_feature_exists = True

            attrs = {target_idx: in_feature[source_idx] for target_idx, source_idx in mapping.items()}

            geom = QgsGeometry()

            if in_feature.hasGeometry() and target.isSpatial():
                # Convert geometry to match destination layer
                # Adapted from QGIS qgisapp.cpp, pasteFromClipboard()
                geom = in_feature.geometry()

                if destType != QgsWkbTypes.UnknownGeometry:
                    newGeometry = geom.convertToType(destType, destIsMulti)

                    if newGeometry.isNull():
                        continue
                    geom = newGeometry

                # Avoid intersection if enabled in digitize settings
                geom.avoidIntersections(QgsProject.instance().avoidIntersectionsLayers())

            if target_feature_exists and action_on_duplicate == self.UPDATE_EXISTING_FEATURE:
                for t_f in target.getFeatures(target_value_dict[in_feature[source_field_unique_values]]):
                    updated_features[t_f.id()] = attrs
                    if target.isSpatial():
                        updated_geometries[t_f.id()] = geom
            else:
                new_feature = QgsVectorLayerUtils().createFeature(target, geom, attrs)
                new_features.append(new_feature)

            feedback.setProgress(int(current * total))

        # Do the Copy and Paste
        res_add_features = False
        try:
            # This might print error messages... But, hey! That's what we want!
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
            return {self.OUTPUT: None}


        if action_on_duplicate == self.SKIP_FEATURE:
            feedback.pushInfo("\nSKIPPED FEATURES: {} duplicate features were skipped while copying features to '{}'!".format(
                skipped_features_count,
                target.name()
            ))

        if action_on_duplicate == self.UPDATE_EXISTING_FEATURE:
            feedback.pushInfo("\nUPDATED FEATURES: {} out of {} duplicate features were updated while copying features to '{}'!".format(
                updated_features_count,
                duplicate_features_count,
                target.name()
            ))

        if not new_features:
            feedback.pushInfo("\nFINISHED WITHOUT APPENDED FEATURES: There were no features to append to '{}'.".format(
                target.name()
            ))
        else:
            if res_add_features:
                feedback.pushInfo("\nSUCCESS: {} out of {} features from input layer were successfully appended to '{}'!".format(
                    len(new_features),
                    source.featureCount(),
                    target.name()
                ))
            else: # TODO do we really need this else message below?
                feedback.reportError("\nERROR: The {} features from input layer could not be appended to '{}'. Sometimes this might be due to NOT NULL constraints that are not met.".format(
                    source.featureCount(),
                    target.name()
                ))

        return {self.OUTPUT: target}
