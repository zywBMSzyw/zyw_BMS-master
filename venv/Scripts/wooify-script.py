#!F:\2018.9.14BMS\BMS-master\BMS-master\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'wooey==0.9.11','console_scripts','wooify'
__requires__ = 'wooey==0.9.11'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('wooey==0.9.11', 'console_scripts', 'wooify')()
    )
