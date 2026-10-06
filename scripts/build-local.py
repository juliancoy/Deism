#!/usr/bin/env python3
"""Regenerate the current source with the exporter's Python and Graphviz runtime."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[1]
image = 'deism-local-builder'
subprocess.run(['docker', 'build', '-t', image, '-f', str(root / 'scripts/Dockerfile.build'), str(root / 'scripts')], check=True)
subprocess.run(['docker', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
                '-v', f'{root}:/workspace', image], check=True)
