import os
import tempfile
from shutil import copyfile

from qgis.core import QgsApplication
from qgis.analysis import QgsNativeAlgorithms
import qgis.utils

import processing

from qgis.testing.mocked import get_iface

# def get_iface():
#     global iface
#
#     def rewrite_method():
#         return "I'm rewritten"
#     iface.rewrite_method = rewrite_method
#     return iface

def get_test_path(path):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, "resources", path)

def get_test_file_copy_path(path):
    src_path = get_test_path(path)
    dst_path = os.path.split(src_path)
    dst_path = os.path.join(dst_path[0], next(tempfile._get_candidate_names()) + dst_path[1])
    print("###", src_path, dst_path)
    copyfile(src_path, dst_path)
    return dst_path

def import_processing():
    global iface
    plugin_found = "processing" in qgis.utils.plugins
    if not plugin_found:
        processing_plugin = processing.classFactory(iface)
        qgis.utils.plugins["processing"] = processing_plugin
        qgis.utils.active_plugins.append("processing")

        from processing.core.Processing import Processing
        Processing.initialize()
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())