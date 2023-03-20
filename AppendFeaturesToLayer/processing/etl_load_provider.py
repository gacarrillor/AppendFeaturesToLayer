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
from qgis.core import QgsProcessingProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from AppendFeaturesToLayer.processing.algs.AppendFeaturesToLayer import AppendFeaturesToLayer


class ETLLoadAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        # Activate provider by default
        ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_ETL_LOAD',
                                            'Activate', True))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        ProcessingConfig.removeSetting('ACTIVATE_ETL_LOAD')

    def isActive(self):
        """Return True if the provider is activated and ready to run algorithms"""
        return ProcessingConfig.getSetting('ACTIVATE_ETL_LOAD')

    def setActive(self, active):
        ProcessingConfig.setSettingValue('ACTIVATE_ETL_LOAD', active)

    def id(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return 'etl_load'

    def name(self):
        """This is the localised full name.
        """
        return 'ETL_LOAD'

    def icon(self):
        """We return the default icon.
        """
        return QgsProcessingProvider.icon(self)

    def loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        for alg in [AppendFeaturesToLayer()]:
            self.addAlgorithm(alg)
