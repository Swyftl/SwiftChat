import os
import shutil
import sys
from pathlib import Path

def build_client():
    print("Building SwiftChat Client...")
    os.system('python -m nuitka --follow-imports --enable-plugin=pyqt6 '
              '--include-package=encryption '
              '--include-package=profiles '
              '--include-data-dir=resources=resources '
              '--windows-disable-console '
              '--standalone client.py')

def build_server():
    print("Building SwiftChat Server...")
    os.system('python -m nuitka --follow-imports --enable-plugin=pyqt6 '
              '--include-package=encryption '
              '--windows-disable-console '
              '--standalone server.py')

def copy_resources():
    # Ensure resources directory exists in the build
    client_build = Path("client.dist")
    if client_build.exists():
        resources_dir = client_build / "resources"
        if not resources_dir.exists():
            shutil.copytree("resources", resources_dir)

if __name__ == "__main__":
    build_client()
    build_server()
    copy_resources()
