#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

''' script to package python code for aws lambda '''

import sys
import os
import json
import tempfile
import hashlib
import base64
import subprocess
import zipfile
import re
from setuptools import find_packages

def _find_root_modules(path):
    return [f for f in os.listdir(path) if re.match(r'^.*\.py$', f)]

def _md5File(path):
    '''return package hash'''
    md5 = hashlib.md5()
    with open(path, 'rb') as output_filename:
        for block in iter(lambda: output_filename.read(65536), b''):
            md5.update(block)
    return md5.hexdigest()

class Packager:
    ''' main class '''

    def __init__(self, path, requirements=None, build_dir=None):
        self.path = path
        self.requirements = requirements
        self.build_dir = build_dir

    def package(self):
        '''find and append packages to lambda zip file'''
        build_path = os.path.abspath(self.build_dir) if self.build_dir else tempfile.mkdtemp(suffix='lambda-packager')
        if not os.path.exists(build_path):
            os.makedirs(build_path)

        output_filename = os.path.join(build_path, 'lambdas.zip')

        packages = [pkg for pkg in find_packages(where=self.path, exclude=['tests', 'test']) if "." not in pkg]
        packages = packages + _find_root_modules(self.path)

        with zipfile.ZipFile(output_filename, 'w') as myzip:
            for module in packages:
                module_relpath = os.path.join(self.path, module)
                if os.path.isdir(module_relpath):
                    for base, _, files in os.walk(module_relpath, followlinks=True):
                        for file_name in files:
                            if not file_name.endswith('.pyc'):
                                path = os.path.join(base, file_name)
                                myzip.write(path, path.replace(self.path, ''))
                else:
                    myzip.write(module_relpath, module)

        output_hash = _md5File(output_filename)

        # install deps if specified
        if os.path.isfile(self.requirements):
            deps_path = os.path.join(build_path, 'deps')
            fnull = open(os.devnull, 'w')
            subprocess.check_call([
                'pip',
                'install',
                '-r',
                self.requirements,
                '-t',
                deps_path
            ], stdout=fnull)

            # zip deps files together for distribution
            with zipfile.ZipFile(output_filename, 'a') as myzip:
                for base, _, files in os.walk(deps_path, followlinks=True):
                    for file in files:
                        path = os.path.join(base, file)
                        myzip.write(path, path.replace(deps_path + '/', ''))

            output_hash += _md5File(self.requirements)

        output_hash = hashlib.sha256(output_hash.encode('utf-8')).digest()
        return {
            'output_filename': os.path.abspath(output_filename),
            'output_base64sha256': base64.b64encode(output_hash).decode('utf-8')
        }

def main():
    '''parse args and package code'''
    args = json.load(sys.stdin)
    packager = Packager(**args)
    output = packager.package()
    json.dump(output, sys.stdout)

if __name__ == '__main__':
    main()
