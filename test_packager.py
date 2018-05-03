#pylint:disable=missing-docstring
import unittest
import zipfile
import time
import os

import packager

def do_packaging(path, deps_filename='', output_filename='lambda_package.zip'):
    '''runner function'''
    pkgr = packager.Packager(path, deps_filename, output_filename)
    pkgr.package()
    output = pkgr.output()
    zipped_filename = zipfile.ZipFile(output['output_filename'], 'r')
    zip_contents = {}
    for name in zipped_filename.namelist():
        zip_contents[name] = zipped_filename.read(name)
    zipped_filename.close()
    return {
        'output': output,
        'zip_contents': zip_contents
    }

class TestPackager(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        try:
            os.remove('lambda_package.zip')
        except FileNotFoundError:
            pass

    def test_pkg_py_deps(self):
        result = do_packaging(
            path='test/python-simple',
            deps_filename='test/deps.zip'
        )
        self.assertEqual(result['zip_contents']['foo.py'], b'# Hello, Python!\n')
        self.assertEqual(result['zip_contents']['deps.py'], b'#dependency code here\n')

    def test_pkg_py_deps_sha(self):

        result1 = do_packaging(
            path='test/python-simple',
            deps_filename='test/deps.zip'
        )
        time.sleep(2) # Allow for current time to 'infect' result
        result2 = do_packaging(
            path='test/python-simple/',
            deps_filename='test/deps.zip'
        )
        self.assertEqual(result1['output']['output_base64sha256'],
                         result2['output']['output_base64sha256'])

    def test_pkg_py_no_deps(self):
        result = do_packaging(
            path='test/python-simple/'
        )
        self.assertEqual(result['zip_contents']['foo.py'], b'# Hello, Python!\n')

    def test_pkg_py_no_deps_sha(self):

        result1 = do_packaging(
            path='test/python-simple/',
            deps_filename='test/deps.zip'
        )
        time.sleep(2) # Allow for current time to 'infect' result
        result2 = do_packaging(
            path='test/python-simple/',
            deps_filename='test/deps.zip'
        )
        self.assertEqual(result1['output']['output_base64sha256'],
                         result2['output']['output_base64sha256'])

    def test_no_pkg_missing_deps(self):
        with self.assertRaises(FileNotFoundError):
            do_packaging(
                path='test/python-simple/',
                deps_filename='non_existent.zip'
            )

    def test_pkg_py_complex(self):
        result = do_packaging(
            path='test/python-complex',
            deps_filename='test/deps.zip'
        )
        self.assertEqual(result['zip_contents']['laughers/haha.py'],
                         b'def haha():\n    print("haha")\n')
        self.assertEqual(result['zip_contents']['deps.py'], b'#dependency code here\n')
        for file_name in result['zip_contents']:
            self.assertFalse(file_name.endswith('.pyc'))

    def test_pkg_py_complex_sha(self):

        result1 = do_packaging(
            path='test/python-complex',
            deps_filename='test/deps.zip'
        )
        time.sleep(2) # Allow for current time to 'infect' result
        result2 = do_packaging(
            path='test/python-complex/',
            deps_filename='test/deps.zip'
        )
        self.assertEqual(result1['output']['output_base64sha256'],
                         result2['output']['output_base64sha256'])
