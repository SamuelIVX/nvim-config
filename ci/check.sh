#!/bin/sh
# Restore, repeat, verify, and purge in an isolated non-root CI home.
set -eu
export PATH="$HOME/.local/bin:$PATH"
python3 -m unittest discover -s tests -p 'test_*.py'
python3 setup.py plan --install-tools
python3 setup.py apply --install-tools
python3 setup.py apply --install-tools
python3 setup.py verify --lsp
sh -n bin/nv
python3 - <<'PY'
import subprocess
import setup
p = setup.profile_paths()
assert setup.version_of('nvim') < (0, 12, 0), 'CI must retain the old default nvim'
assert subprocess.check_output([str(setup.REPO/'bin/nv'),'--version'],text=True).startswith('NVIM v0.12.')
receipt = (p['state']/'setup.json').read_bytes()
mtime = (p['state']/'setup.json').stat().st_mtime_ns
subprocess.run(['python3','setup.py','apply','--install-tools'],check=True)
assert (p['state']/'setup.json').read_bytes() == receipt
assert (p['state']/'setup.json').stat().st_mtime_ns == mtime
assert not subprocess.check_output(['git','status','--porcelain'],text=True)
PY
python3 setup.py remove
python3 setup.py apply --install-tools
python3 setup.py remove --purge
python3 - <<'PY'
import os
import setup
p = setup.profile_paths()
for name in ('config','data','state','cache','launcher'):
    assert not os.path.lexists(p[name]), p[name]
assert (setup.REPO/'init.lua').is_file()
assert setup.version_of('nvim') < (0, 12, 0)
print('Fresh restore, repeat apply, LSP verification, and purge passed')
PY
