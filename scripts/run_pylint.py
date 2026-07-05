#!/usr/bin/env python3
"""运行 Pylint 检查项目代码质量。

Usage:
    python scripts/run_pylint.py              # 检查所有文件
    python scripts/run_pylint.py app          # 检查 app 目录
    python scripts/run_pylint.py app/llms     # 检查特定子目录
    python scripts/run_pylint.py main.py      # 检查单个文件
"""

import sys
import subprocess
from pathlib import Path


def run_pylint(targets=None):
    """运行 Pylint 检查。

    Args:
        targets: 要检查的目标路径列表，默认检查 app/, tests/, main.py

    Returns:
        int: Pylint 退出码
    """
    project_root = Path(__file__).parent.parent

    # 默认检查目标
    if not targets:
        targets = ["app", "tests", "main.py", "scripts"]

    # 过滤存在的目标
    valid_targets = []
    for target in targets:
        target_path = project_root / target
        if target_path.exists():
            valid_targets.append(str(target_path))
        else:
            print(f"⚠️  警告: 目标 '{target}' 不存在，已跳过")

    if not valid_targets:
        print("❌ 错误: 没有找到有效的检查目标")
        return 1

    print(f"🔍 运行 Pylint 检查: {', '.join(valid_targets)}")
    print("-" * 60)

    # 构建 pylint 命令
    cmd = [
        sys.executable, "-m", "pylint",
        "--rcfile", str(project_root / ".pylintrc"),
        *valid_targets
    ]

    # 运行 pylint
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ 错误: 未找到 pylint，请先安装:")
        print("   pip install pylint")
        return 1


def main():
    """主入口函数。"""
    # 从命令行获取目标
    targets = sys.argv[1:] if len(sys.argv) > 1 else None

    exit_code = run_pylint(targets)

    print("-" * 60)
    if exit_code == 0:
        print("✅ Pylint 检查通过!")
    else:
        print(f"⚠️  Pylint 检查完成，退出码: {exit_code}")
        print("   (评分 10/10 = 退出码 0，评分越低退出码越高)")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
