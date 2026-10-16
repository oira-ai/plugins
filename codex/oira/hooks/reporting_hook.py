"""Manual-route entry point. Bundled setup installs an absolute Oira launcher.

Implementation is generated from cli/oira_runtime; no independent state writer.
"""
from pathlib import Path
import sys
if (Path(__file__).parent / 'oira_hooks.py').is_file():
    sys.path.insert(0, str(Path(__file__).parent))
    from oira_hooks import *  # noqa: F403
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cli'))
    from oira_runtime.hooks import *  # noqa: F403
if __name__ == '__main__':
    raise SystemExit(main())  # noqa: F405
