import os
import posixpath
import subprocess
import sys
import urllib

import requests


def report_and_check_call(**kwargs):
    print('\nCalling: ')

    for kwarg in ('command', 'cwd'):
        if kwarg in kwargs:
            print('    {}: {}'.format(kwarg, kwargs[kwarg]))

    # may only be required on AppVeyor
    sys.stdout.flush()

    command = kwargs.pop('command')

    subprocess.check_call(command, **kwargs)


def save_url_to_file(
        url, file_path=None, file_name=None, block_size=1024, **kwargs):
    #https://stackoverflow.com/questions/14114729/save-a-large-file-using-the-python-requests-library/14114741#14114741

    response = requests.get(url, **kwargs, stream=True)

    # Throw an error for bad status codes
    response.raise_for_status()

    if file_path is None:
        file_path = '.'

    if file_name is None:
        file_name = posixpath.basename(urllib.parse.urlparse(url).path)

    path = os.path.join(file_path, file_name)
    with open(path, 'wb') as handle:
        for block in response.iter_content(block_size):
            handle.write(block)

    return path
