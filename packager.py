#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

import sys
import os
import subprocess
import json
import shutil
import hashlib
import base64
import tempfile
import zipfile
import re
from setuptools import find_packages

class Packager:
    def __init__(self, path, output_filename='lambda.zip', extra_files=None):
        self.path = path
        self.output_filename = os.path.join(os.curdir, output_filename)
        self.extra_files = extra_files

    def package(self):

        build_path = tempfile.mkdtemp(suffix='lambda-packager')

        # install packages
        requirements_file = os.path.join(self.path, 'requirements.txt')
        if os.path.isfile(requirements_file):
            fnull = open(os.devnull, 'w')
            subprocess.check_call([
                'pip',
                'install',
                '-r',
                requirements_file,
                '-t',
                build_path
            ], stdout=fnull)


        packages = find_packages(where=self.path,
                                 exclude=['tests', 'test']) + self._find_root_modules(self.path)

        for module in packages:
            src = os.path.join(self.path, module)
            dst = os.path.join(build_path, module)
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.pyc'))
            elif os.path.isfile(src):
                shutil.copy(src, dst)


        # zip together for distribution
        with zipfile.ZipFile(self.output_filename, 'w') as myzip:
            for base, _, files in os.walk(build_path, followlinks=True):
                for file in files:
                    path = os.path.join(base, file)
                    myzip.write(path, path.replace(build_path + '/', ''))

    def output_base64sha256(self):
        sha256 = hashlib.sha256()
        with open(self.output_filename, 'rb') as f:
            for block in iter(lambda: f.read(65536), b''):
                sha256.update(block)
        return base64.b64encode(sha256.digest()).decode('utf-8')

    def output(self):
        return {
            "code": self.path,
            "output_filename": self.output_filename,
            "output_base64sha256": self.output_base64sha256()
        }

    def _find_root_modules(self, path):
        return [f for f in os.listdir(path) if re.match(r'^.*\.py$', f)]

def main():
    args = json.load(sys.stdin)
    packager = Packager(**args)
    packager.package()
    json.dump(packager.output(), sys.stdout)

if __name__=='__main__':
    main()
