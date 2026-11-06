# Deployed native baseline

`legacy-kit.tar.gz` is the exact server kit from source commit `031f3ae`, SHA-256 `c50a99730f83a16e994f941006f2b64b7943b12f6fd60f0d3c087481208d3537`. It contains the original Mordor distribution and its original copyright notices.

`install-ubuntu.sh` and `enable-public.py` are the corresponding historical installer scripts. `recovered-runtime.py` is the bounded save/quit repair from commit `5a21610`, before advanced command smoke tests were added. These historical files are generator inputs, not instructions to reinstall a working game.

`baseline.json` records their SHA-256 hashes, the original service unit, and the repaired runtime test hash. Native-update generation verifies the metadata and kit before use, without requiring historical Git objects. The recovery generator uses the historical scripts and repaired test. Do not modify these pinned baseline files to accommodate local edits on a live server.
