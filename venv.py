#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys

from distutils.core import run_setup


def main():
    # TODO: CAMPid 097541134161236179854863478319
    try:
        import pip
    except ImportError:
        print('')
        print('')
        print('    pip not installed:')
        print('')
        print('        Use your package manager to install')
        print('')
        print('        e.g. sudo apt-get install python3-pip')
        print('')

        return 1

    # TODO: redo as a bootstrap script
    #       https://virtualenv.readthedocs.org/en/latest/reference.html#extending-virtualenv

    parser = argparse.ArgumentParser()
    #parser.add_argument('--pyqt5')
    #parser.add_argument('--pyqt5-plugins')
    parser.add_argument('--bin')
    parser.add_argument('--activate')
    parser.add_argument('--no-ssl-verify', action='store_true')
    parser.add_argument('--virtualenv', '--venv', default='venv')
    parser.add_argument('--in-virtual', action='store_true')
    parser.add_argument('--rebuild', action='store_true')

    args = parser.parse_args()

    # TODO: let this be the actual working directory
    myfile = os.path.realpath(__file__)
    mydir = os.path.dirname(myfile)

    # TODO: CAMPid 9811163648546549994313612126896
    def pip_install(package, no_ssl_verify, virtual=False):
        pip_parameters = ['install']
        if no_ssl_verify:
            pip_parameters.append('--index-url=http://pypi.python.org/simple/')
            pip_parameters.append('--trusted-host')
            pip_parameters.append('pypi.python.org')
        if not virtual:
            pip_parameters.append('--user')
        pip_parameters.append(package)
        return pip.main(pip_parameters)

    if not args.in_virtual:
        if args.rebuild:
            shutil.rmtree(args.virtualenv, ignore_errors=True)

        try:
            os.mkdir(args.virtualenv)
        except FileExistsError:
            print('')
            print('')
            print('    Directory already exists and must be deleted to create the virtual environment')
            print('')
            print('        {args.virtualenv}'.format(**locals()))
            print('')

            return 1

        # TODO: test/add linux support
        if sys.platform not in ['win32']:
            raise Exception("Unsupported sys.platform: {}".format(sys.platform))

        if sys.platform == 'win32':
            bin = 'Scripts'
        else:
            bin = 'bin'
        bin = os.path.join(args.virtualenv, bin)

        activate = os.path.join(bin, 'activate')

        pip_install('virtualenv', args.no_ssl_verify)

        virtualenv_command = [sys.executable, '-m', 'virtualenv', '--system-site-packages', args.virtualenv]
        returncode = subprocess.call(virtualenv_command)

        if returncode != 0:
            raise Exception("Received return code {} when running {}"
                            .format(result.returncode, virtualenv_command))

        virtualenv_python = os.path.realpath(os.path.join(bin, 'python'))
        virtualenv_python_command = [virtualenv_python,
                                     myfile,
                                     '--bin', bin,
                                     '--activate', activate,
                                     '--in-virtual']
        if args.no_ssl_verify:
            virtualenv_python_command.append('--no-ssl-verify')

        returncode = subprocess.call(virtualenv_python_command)

        return returncode
    else:
        # TODO: CAMPid 935481834121236136785436129254676532
        def setup(path):
            backup = os.getcwd()
            os.chdir(path)
            run_setup(os.path.join(path, 'setup.py'), script_args=['develop'])
            os.chdir(backup)

        src = os.path.join(mydir, args.virtualenv, 'src')
        os.makedirs(src, exist_ok=True)

        zip_repos = {
        }

        packages = [
            'requests',
            'vcversioner==2.16.0.0',
            'requests==2.13.0',
            'pyqtdeploy==1.3.2',
            'PyQt5=5.8.2',
        ]
        # TODO: make this configurable
        custom_packages = [
            'wheel',
            #            'gitpython'
        ]
        for package in packages + custom_packages:
            pip_install(package, args.no_ssl_verify, virtual=True)

        import requests
        import zipfile
        import io
        for name, url in zip_repos.items():
            try:
                response = requests.get(url, verify=not args.no_ssl_verify)
            except requests.exceptions.SSLError:
                print('')
                print('        SSL error occurred while requesting:')
                print('            {}'.format(url))
                print('')
                print('        You probably want to use --no-ssl-verify')
                print('')

                return 1

            zip_data = io.BytesIO()
            zip_data.write(response.content)
            zip_file = zipfile.ZipFile(zip_data)
            zip_dir = os.path.split(zip_file.namelist()[0])[0]
            zip_file.extractall(path=src)
            shutil.move(os.path.join(src, zip_dir),
                        os.path.join(src, name))
            setup(os.path.join(src, name))

        # TODO: Figure out why this can't be moved before other installs
        #       Dependencies maybe?
#        setup(mydir)

        activate = args.activate
        if sys.platform == 'win32':
            with open(os.path.join(mydir, 'activate.bat'), 'w') as f:
                activate = activate.replace('\\', '/')
                f.write('{}\n'.format(activate))

        with open(os.path.join(mydir, 'activate'), 'w', newline='') as f:
            f.write('source {}\n'.format(activate))

        print('')
        print('')
        print('    To use the new virtualenv:')
        print('')
        print('        posix: source activate')
        if sys.platform == 'win32':
            print('        win32: activate')
        print('')

        return 0


if __name__ == '__main__':
    sys.exit(main())
