# -*- coding: utf-8 -*-
"""
PyInstaller 打包脚本 - 生成免安装文件夹版 .exe（含 Playwright 浏览器引擎）
使用方法：python build_app.py
"""
import os
import sys
import shutil

APP_DIR     = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(APP_DIR, "dist")
CHROMIUM_SRC = r"C:\Users\wangd\AppData\Local\ms-playwright\chromium-1217"
CHROMIUM_DST = "_playwright_browser"

# Python 及 PyInstaller 均在当前 Python 环境中可用
PYTHON_EXE = sys.executable   # 当前 python.exe

def build():
    # 清理旧产物
    for d in ["build", OUTPUT_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    print("=" * 60)
    print("  卫健法律法规检索系统 - 打包工具 (含浏览器引擎)")
    print("=" * 60)
    print(f"\nPython:    {PYTHON_EXE}")
    print(f"Chromium:  {CHROMIUM_SRC}")

    # -------- PyInstaller 参数 ----------
    spec_args = [
        os.path.join(APP_DIR, "main.py"),
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "卫健法律法规检索系统",
        "--add-data", f"{os.path.join(APP_DIR, 'builtin_laws.py')};.",
        "--add-data", f"{os.path.join(APP_DIR, 'searcher.py')};.",
        "--add-data", f"{os.path.join(APP_DIR, 'doc_generator.py')};.",
        "--hidden-import", "builtin_laws",
        "--hidden-import", "searcher",
        "--hidden-import", "doc_generator",
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        "--hidden-import", "bs4.dammit",
        "--hidden-import", "bs4.builder",
        "--hidden-import", "soupsieve",
        "--hidden-import", "lxml",
        "--hidden-import", "lxml.etree",
        "--hidden-import", "docx",
        "--hidden-import", "urllib3",
        "--hidden-import", "playwright",
        "--hidden-import", "playwright.async_api",
        "--collect-submodules", "bs4",
        "--collect-submodules", "soupsieve",
        "--collect-submodules", "lxml",
        "--collect-submodules", "playwright",
        "--collect-submodules", "docx",
        "--collect-data", "bs4",
        "--collect-data", "soupsieve",
        "--collect-data", "playwright",
        "--collect-data", "docx",
        "--distpath", OUTPUT_DIR,
        "--workpath", os.path.join(APP_DIR, "build"),
        "--specpath", APP_DIR,
    ]

    print("\n步骤1: PyInstaller 打包...\n")

    # 直接调用 PyInstaller 主函数（避免子进程编码问题）
    from PyInstaller import __main__ as pyi_main
    # 保存并替换 sys.argv
    old_argv = sys.argv[:]
    sys.argv = [sys.executable, "-y"] + [a for a in spec_args if a]
    try:
        pyi_main.run()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv

    # 判断打包是否成功
    exe_dir = os.path.join(OUTPUT_DIR, "卫健法律法规检索系统")
    exe_path = os.path.join(exe_dir, "卫健法律法规检索系统.exe")
    if not os.path.exists(exe_path):
        print("\n[FAIL] PyInstaller 打包失败，未生成 exe")
        return False

    print("\n步骤2: 嵌入 Chromium 浏览器...")
    chrom_dst = os.path.join(exe_dir, CHROMIUM_DST)
    if os.path.exists(CHROMIUM_SRC):
        print(f"  源:  {CHROMIUM_SRC}")
        print(f"  目标: {chrom_dst}")
        if os.path.exists(chrom_dst):
            shutil.rmtree(chrom_dst, ignore_errors=True)
        shutil.copytree(
            CHROMIUM_SRC, chrom_dst,
            symlinks=False,
            ignore_dangling_symlinks=True,
            dirs_exist_ok=True
        )
        print("  浏览器嵌入完成")
    else:
        print(f"  [跳过] Chromium 未找到: {CHROMIUM_SRC}")

    total_mb = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fns in os.walk(exe_dir)
        for f in fns
    ) / (1024 * 1024)

    print(f"\n{'=' * 60}")
    print("  [OK] 打包完成！")
    print(f"  启动文件: {exe_path}")
    print(f"  总大小:   {total_mb:.0f} MB")
    print(f"{'=' * 60}")
    print("\n使用说明：")
    print("  1. 打开 '卫健法律法规检索系统' 文件夹")
    print("  2. 双击 '卫健法律法规检索系统.exe' 运行")
    print("  3. 无需安装任何依赖，首次启动可能稍慢（加载浏览器引擎）")

    # 清理 .spec 文件
    spec = os.path.join(APP_DIR, "卫健法律法规检索系统.spec")
    if os.path.exists(spec):
        os.remove(spec)
    return True

if __name__ == "__main__":
    build()
