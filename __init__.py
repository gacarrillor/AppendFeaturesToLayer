# -*- coding: utf-8 -*-
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
def classFactory(iface):
    from .append_features_to_layer_plugin import AppendFeaturesToLayerPlugin
    return AppendFeaturesToLayerPlugin(iface)
