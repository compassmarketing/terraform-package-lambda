#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

''' script to package python code for aws lambda '''

import sys
import os
import json
import hashlib
import glob
import subprocess
import zipfile
import re
from setuptools import find_packages

def _find_root_modules(path):
    return [f for f in os.listdir(path) if re.match(r'^.*\.py$', f)]

def _sha256File(path):
    '''return package hash'''
    sha256 = hashlib.sha256()
    with open(path, 'rb') as output_filename:
        for block in iter(lambda: output_filename.read(65536), b''):
            sha256.update(block)
    return sha256.hexdigest()

class Packager:
    ''' main class '''

    def __init__(self, path, build_dir, requirements=None):
        self.path = path
        self.requirements = requirements
        self.build_dir = build_dir

    def package(self):
        '''find and append packages to lambda zip file'''
        build_path = os.path.abspath(self.build_dir)
        if not os.path.exists(build_path):
            os.makedirs(build_path)
        else:
            for f in glob.glob(os.path.join(build_path, '*.zip')):
                os.remove(f)

        output_filename = os.path.join(build_path, 'lambdas.zip')

        packages = [pkg for pkg in find_packages(where=self.path, exclude=['tests', 'test']) if "." not in pkg]
        packages = packages + _find_root_modules(self.path)

        with zipfile.ZipFile(output_filename, 'w') as myzip:
            for module in packages:
                module_relpath = os.path.join(self.path, module)
                if os.path.isdir(module_relpath):
                    for base, _, files in os.walk(module_relpath, followlinks=True):
                        for file_name in files:
                            if file_name.endswith('.py'):
                                path = os.path.join(base, file_name)
                                myzip.write(path, path.replace(self.path, ''))
                else:
                    myzip.write(module_relpath, module)

        output_hash = _sha256File(output_filename)

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

            dep_hash =  _sha256File(self.requirements)
            output_hash = hashlib.sha256((output_hash + dep_hash).encode('utf-8')).hexdigest()

        hashed_filename = output_hash + '.zip'
        os.rename(output_filename, os.path.join(build_path, hashed_filename))
        return {
            'output_filename': hashed_filename
        }

def main():
    '''parse args and package code'''
    args = json.load(sys.stdin)
    packager = Packager(**args)
    output = packager.package()
    json.dump(output, sys.stdout)

if __name__ == '__main__':
    main()
