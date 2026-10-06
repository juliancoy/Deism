#!/usr/bin/env python3
"""Regenerate the current source with the exporter's Python and Graphviz runtime."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[1]
image = 'deism-local-builder'
if subprocess.run(['docker', 'image', 'inspect', image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
    raise SystemExit('Missing exporter runtime. Provision deism-local-builder once before exporting; normal updates only write the mounted build directory.')
subprocess.run(['docker', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
                '-v', f'{root}:/workspace', image], check=True)
