"""Desktop runner for Estoque de Cimento (Windows offline).

Starts the Django backend on localhost using Waitress, applying migrations on startup.
Intended to be packaged into an .exe (PyInstaller) and launched by the desktop shell.

Environment variables (optional):
- ESTOQUE_CIMENTO_DESKTOP=1
- ESTOQUE_CIMENTO_PORT=8000
- ESTOQUE_CIMENTO_DATA_DIR=<dir>     (where db.sqlite3 will live)
- ESTOQUE_CIMENTO_FRONTEND_DIST=<dir> (Vite dist served by Django in desktop mode)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_env_defaults() -> int:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    os.environ.setdefault('ESTOQUE_CIMENTO_DESKTOP', '1')

    port_str = os.environ.get('ESTOQUE_CIMENTO_PORT') or '8000'
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    # Default data dir: alongside executable/project (caller should override in production)
    os.environ.setdefault('ESTOQUE_CIMENTO_DATA_DIR', str(Path.cwd()))
    return port


def main() -> int:
    port = _ensure_env_defaults()

    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application

    # Ensure DB schema exists
    call_command('migrate', interactive=False, verbosity=0)

    application = get_wsgi_application()

    from waitress import serve

    serve(application, host='127.0.0.1', port=port, threads=8)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
