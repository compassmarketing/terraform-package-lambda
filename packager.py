#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

''' script to package python code for aws lambda '''

import sys
import os
import json
import shutil
import hashlib
import base64
#import subprocess
import zipfile
import re
from setuptools import find_packages

def _find_root_modules(path):
    return [f for f in os.listdir(path) if re.match(r'^.*\.py$', f)]


class Packager:
    ''' main class '''
    # default deps_filename to '' because terraform does not support null values for variables
    def __init__(self, path, deps_filename='', output_filename='lambda_package.zip'):
        self.path = path
        self.output_filename = os.path.join(os.curdir, output_filename)
        self.deps_filename = os.path.join(os.curdir, deps_filename) if deps_filename != '' else None

        #check that lambda_package.zip already exists
        if self.deps_filename and not os.path.isfile(self.deps_filename):
            raise FileNotFoundError(self.deps_filename)

    def package(self):
        '''find and append packages to lambda zip file'''

        # copy deps file into package file
        if self.deps_filename:
            shutil.copy(self.deps_filename, self.output_filename)

        packages = [pkg for pkg in find_packages(where=self.path, exclude=['tests', 'test']) if '.' not in pkg]
        packages = packages + _find_root_modules(self.path)

        with zipfile.ZipFile(self.output_filename, 'a') as myzip:
            for module in packages:
                module_relpath = os.path.join(self.path, module)
                if os.path.isdir(module_relpath):
                    for base, _, files in os.walk(module_relpath, followlinks=True):
                        for file_name in files:
                            if not file_name.endswith('.pyc'):
                                path = os.path.join(base, file_name)
                                print(path)
                                myzip.write(path, path.replace(self.path, ''))
                else:
                    myzip.write(module_relpath, module)

    def output_base64sha256(self):
        '''return package hash'''
        sha256 = hashlib.sha256()
        with open(self.output_filename, 'rb') as output_filename:
            for block in iter(lambda: output_filename.read(65536), b''):
                sha256.update(block)
        return base64.b64encode(sha256.digest()).decode('utf-8')

    def output(self):
        '''provide data for terraform output'''
        return {
            'path': self.path,
            'output_filename': self.output_filename,
            'output_base64sha256': self.output_base64sha256()
        }

def main():
    '''parse args and package code'''
    args = json.load(sys.stdin)
    packager = Packager(**args)
    packager.package()
    json.dump(packager.output(), sys.stdout)

if __name__ == '__main__':
    main()
