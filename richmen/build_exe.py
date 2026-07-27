#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def build():
    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

    pyinstaller = shutil.which("pyinstaller")
    if not pyinstaller:
        pyinstaller = shutil.which("pyinstaller.exe")
    if not pyinstaller:
        print("错误: 未找到 PyInstaller，请先运行: pip install pyinstaller")
        sys.exit(1)

    base_cmd = [
        pyinstaller,
        "--noconfirm",
        "--clean",
    ]

    print("=" * 60)
    print("构建服务器 RichMen_Server.exe...")
    print("=" * 60)
    subprocess.run(base_cmd + [
        "--name", "RichMen_Server",
        "--onefile",
        "--console",
        "--add-data", f"common{os.pathsep}common",
        "--add-data", f"server{os.pathsep}server",
        "run_server.py",
    ], check=True)

    print()
    print("=" * 60)
    print("构建客户端 RichMen_Client.exe...")
    print("=" * 60)
    subprocess.run(base_cmd + [
        "--name", "RichMen_Client",
        "--onefile",
        "--console",
        "--add-data", f"common{os.pathsep}common",
        "--add-data", f"client{os.pathsep}client",
        "--hidden-import", "tkinter",
        "--hidden-import", "asyncio",
        "run_client.py",
    ], check=True)

    print()
    print("=" * 60)
    print("构建完成！")
    print(f"服务器: {os.path.join(dist_dir, 'RichMen_Server.exe')}")
    print(f"客户端: {os.path.join(dist_dir, 'RichMen_Client.exe')}")
    print("=" * 60)

if __name__ == "__main__":
    build()
