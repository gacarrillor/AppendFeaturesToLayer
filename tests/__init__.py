import qgis.core
from qgis.PyQt.sip import SIP_VERSION_STR
from qgis.PyQt.QtCore import QT_VERSION_STR
from qgis.PyQt.Qt import PYQT_VERSION_STR
from qgis.core import Qgis

print("# # # # # # # # # # # # # # #")
print("QGIS version:", Qgis.QGIS_VERSION)
print("Qt version:", QT_VERSION_STR)
print("SIP version:", SIP_VERSION_STR)
print("PyQt version:", PYQT_VERSION_STR)
print("# # # # # # # # # # # # # # #")