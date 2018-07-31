import os
import sys

name = 'QT_BASE_PATH'
print('---')
print(sys.executable)
print(sys.version_info)
print(name, ':', os.environ[name])
print('---')
