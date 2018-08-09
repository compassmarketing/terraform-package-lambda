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
import subprocess
import zipfile
import re
from setuptools import find_packages

def _find_root_modules(path):
    return [f for f in os.listdir(path) if re.match(r'^.*\.py$', f)]

def sha_256_file(path):
    '''return package hash'''
    sha256 = hashlib.sha256()
    with open(path, 'rb') as output_filename:
        for block in iter(lambda: output_filename.read(65536), b''):
            sha256.update(block)
    return sha256.digest()

def zip_directory(filename, src_path, mode='w'):
    with zipfile.ZipFile(filename, mode) as myzip:
        for base, _, files in os.walk(src_path, followlinks=True):
            for file in files:
                path = os.path.join(base, file)
                myzip.write(path, path.replace(src_path + '/', ''), compress_type=zipfile.ZIP_DEFLATED)

class Packager:
    ''' main class '''

    def __init__(self, path, build_dir, requirements=None):
        self.path = path
        self.requirements = requirements
        self.build_dir = build_dir

    def package(self):
        '''find and append packages to lambda zip file'''
        build_path = tempfile.mkdtemp(suffix='lambda-packager')

        packages = [pkg for pkg in find_packages(where=self.path, exclude=['tests', 'test']) if "." not in pkg]
        packages = packages + _find_root_modules(self.path)

        for module in packages:
            src = os.path.join(self.path, module)
            dst = os.path.join(build_path, module)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                shutil.copy(src, dst)

        hashvalues = []
        for root, _, files in os.walk(build_path, topdown=True, followlinks=True):
            hashvalues.extend(
                [sha_256_file(os.path.join(root, f)) for f in files if not f.endswith('.pyc')]
            )

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

            hashvalues.append(sha_256_file(self.requirements))


        sha256 = hashlib.sha256()
        for hashval in sorted(hashvalues):
            sha256.update(hashval)

        output_filename = os.path.join(self.build_dir, f'{sha256.hexdigest()}.zip')
        zip_directory(output_filename, build_path)

        return {
            'output_filename': output_filename
        }

def main():
    '''parse args and package code'''
    args = json.load(sys.stdin)
    packager = Packager(**args)
    output = packager.package()
    json.dump(output, sys.stdout)

if __name__ == '__main__':
    main()
