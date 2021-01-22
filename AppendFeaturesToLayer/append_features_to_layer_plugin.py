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
import os.path
import glob
import shutil

from qgis.core import QgsApplication, QgsProcessingModelAlgorithm, Qgis

from processing.modeler.ModelerUtils import ModelerUtils
from .processing.etl_load_provider import ETLLoadAlgorithmProvider

#from .resources_rc import *

class AppendFeaturesToLayerPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        # Add provider and models to QGIS
        self.provider = ETLLoadAlgorithmProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
        if QgsApplication.processingRegistry().providerById('model'):
            self.add_processing_models(None)
        else: # We need to wait until processing is initialized
            QgsApplication.processingRegistry().providerAdded.connect(self.add_processing_models)

    def initGui(self):
        self.initProcessing()
            
    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def add_processing_models(self, provider_id):
        if not (provider_id == 'model' or provider_id is None):
            return

        if provider_id is not None: # If method acted as slot
            QgsApplication.processingRegistry().providerAdded.disconnect(self.add_processing_models)

        # Add etl-model
        basepath = os.path.dirname(os.path.abspath(__file__))
        plugin_models_dir = os.path.join(basepath, "processing", "models")

        filenames = list()

        # Go for subfolders.
        # We store models that depend on QGIS versions in folders like "314" (for QGIS 3.14.x)
        # This was initially needed for the FieldMapper input, which was migrated to C++ in QGIS 3.14
        qgis_major_version = str(Qgis.QGIS_VERSION_INT)[:3]
        qgis_major_version_path = os.path.join(plugin_models_dir, qgis_major_version)

        if not os.path.isdir(qgis_major_version_path):
            # No folder for this version (e.g., unit tests on QGIS-dev), so let's find the most recent version
            subfolders = [sf.name for sf in os.scandir(plugin_models_dir) if sf.is_dir()]
            if subfolders:
                qgis_major_version_path = os.path.join(plugin_models_dir, max(subfolders))

        for filename in glob.glob(os.path.join(qgis_major_version_path, '*.model3')):
            filenames.append(filename)

        for filename in filenames:
            alg = QgsProcessingModelAlgorithm()
            if not alg.fromFile(filename):
                print("ERROR: Couldn't load model from {}".format(filename))
                return

            destFilename = os.path.join(ModelerUtils.modelsFolders()[0], os.path.basename(filename))
            shutil.copyfile(filename, destFilename)

        QgsApplication.processingRegistry().providerById('model').refreshAlgorithms()
