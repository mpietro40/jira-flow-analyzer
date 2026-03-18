# PyInstaller Hooks

Place custom PyInstaller hook files here (e.g. `hook-mymodule.py`).

PyInstaller will search this directory for hooks before its own built-ins.
Currently no custom hooks are required — the hidden-imports list in
`build_all.py` / `build_executable.py` covers all dependencies.
