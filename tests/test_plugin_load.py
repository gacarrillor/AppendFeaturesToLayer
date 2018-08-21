import qgis
import nose2

from qgis.testing import unittest, start_app

start_app()

class TestPluginLoad(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('setUp test_plugin_load')
        pass

    def test_plugin_load(self):
        print('Validating plugin load...')
        self.assertEqual(1, 1)

    def tearDownClass():
        print('tearDown test_plugin_load')

if __name__ == '__main__':
    nose2.main()
