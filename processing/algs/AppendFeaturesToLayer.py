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
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsProject,
                       QgsVectorLayerUtils
                       )

class AppendFeaturesToLayer(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def createInstance(self):
        return type(self)()

    def group(self):
        return QCoreApplication.translate("AppendFeaturesToLayer", 'Vector table')

    def groupId(self):
        return 'vectortable'

    def tags(self):
        return (QCoreApplication.translate("AppendFeaturesToLayer", 'append,copy,insert,features,paste,etl')).split(',')

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,
                                                              QCoreApplication.translate("AppendFeaturesToLayer", 'Input layer'),
                                                              [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterVectorLayer(self.OUTPUT,
                                                              QCoreApplication.translate("AppendFeaturesToLayer", 'Output layer'),
                                                              [QgsProcessing.TypeVector]))
        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT,
                                                        QCoreApplication.translate("AppendFeaturesToLayer", 'Output layer with new features')))

    def name(self):
        return 'appendfeaturestolayer'

    def displayName(self):
        return QCoreApplication.translate("AppendFeaturesToLayer", 'Append features to layer')

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        target = self.parameterAsVectorLayer(parameters, self.OUTPUT, context)

        # Define a mapping between source and target layer
        mapping = dict()
        for target_idx in target.fields().allAttributesList():
            target_field = target.fields().field(target_idx)
            source_idx = source.fields().indexOf(target_field.name())
            if source_idx != -1:
                mapping[target_idx] = source_idx

        # Copy and Paste
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        destType = target.geometryType()
        destIsMulti = QgsWkbTypes.isMultiType(target.wkbType())
        new_features = []
        for current, in_feature in enumerate(features):
            if feedback.isCanceled():
                break

            attrs = {target_idx: in_feature[source_idx] for target_idx, source_idx in mapping.items()}

            geom = QgsGeometry()

            if in_feature.hasGeometry():
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

            new_feature = QgsVectorLayerUtils().createFeature(target, geom, attrs)
            new_features.append(new_feature)

            feedback.setProgress(int(current * total))

        # This might throw errors and print messages... But, in that case, that's what we want!
        with edit(target):
            res = target.addFeatures(new_features)

        if res:
            feedback.pushInfo("{} out of {} features from input layer were successfully appended to '{}'!".format(
                len(new_features),
                source.featureCount(),
                target.name()
            ))
        else:
            feedback.pushInfo("The {} features from input layer could not be appended to '{}'. This is likely due to NOT NULL constraints that are not met.".format(
                source.featureCount(),
                target.name()
            ))

        return {self.OUTPUT: target}
