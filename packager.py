#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

''' script to package python code for aws lambda '''

import sys
import os
import json
import hashlib
import tempfile
import shutil
import base64
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
    return base64.b64encode(sha256.digest()).decode('utf-8')

class Packager:
    ''' main class '''

    def __init__(self, path, filename, requirements=None):
        self.path = path
        self.requirements = requirements
        self.filename = filename

    def package(self):
        '''find and append packages to lambda zip file'''
        build_path = tempfile.mkdtemp(suffix='lambda-packager')

        # install deps if specified
        if os.path.isfile(self.requirements):
            fnull = open(os.devnull, 'w')
            subprocess.check_call([
                'pip',
                'install',
                '-r',
                self.requirements,
                '-t',
                build_path
            ], stdout=fnull)

        packages = [pkg for pkg in find_packages(where=self.path, exclude=['tests', 'test']) if "." not in pkg]
        packages = packages + _find_root_modules(self.path)

        for module in packages:
            src = os.path.join(self.path, module)
            dst = os.path.join(build_path, module)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copy(src, dst)


        # zip together for distribution
        with zipfile.ZipFile(self.filename, 'w') as myzip:
            for base, _, files in os.walk(build_path, followlinks=True):
                for file in files:
                    if not file.endswith('.pyc') and file != 'lambdas.zip':
                        path = os.path.join(base, file)
                        with open(path, 'rb') as f:
                            zipinfo = zipfile.ZipInfo(path.replace(build_path + '/', ''))
                            myzip.writestr(zipinfo, f.read(), compress_type=zipfile.ZIP_DEFLATED)

        return {
            'output_filename': self.filename,
            'output_base64sha256': _sha256File(os.path.abspath(self.filename))
        }

def main():
    '''parse args and package code'''
    args = json.load(sys.stdin)
    packager = Packager(**args)
    output = packager.package()
    json.dump(output, sys.stdout)

if __name__ == '__main__':
    main()
