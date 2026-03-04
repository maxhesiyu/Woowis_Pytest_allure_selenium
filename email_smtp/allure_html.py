import sys
import subprocess
from pathlib import Path

# 配置抽离到config.py
from config.config import ALLURE_RESULTS, ALLURE_HTML

def check_allure_installed():
    """检查Allure CLI是否安装并配置"""
    try:
        result = subprocess.run(
            ["allure", "--version"],
            shell=True,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            print(f"✅ Allure CLI已安装，版本：{result.stdout.strip()}")
            return True
        else:
            print(f"❌ Allure CLI未安装或配置错误：{result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ 未找到Allure CLI，请先安装并配置环境变量！")
        return False

def generate_allure_report(results_dir: Path, html_dir: Path, clean: bool = True) -> Path:
    """
    生成Allure HTML单文件报告
    :param results_dir: allure-results目录路径
    :param html_dir: allure-html输出目录路径
    :param clean: 是否清理原有报告
    :return: 生成的index.html文件路径
    """
    # 前置检查
    if not check_allure_installed():
        raise RuntimeError("Allure CLI未安装/配置，无法生成报告")
    if not results_dir.exists():
        raise RuntimeError(f"❌ allure-results目录不存在：{results_dir}")
    if len(list(results_dir.glob("*.json"))) == 0:
        raise RuntimeError(f"❌ allure-results目录为空，无测试结果可生成报告")

    # 构建命令
    allure_cmd = [
        "allure", "generate",
        str(results_dir),
        "-o", str(html_dir),
        "--single-file"
    ]
    if clean:
        allure_cmd.append("--clean")

    # 执行生成
    print(f"📝 生成Allure报告命令：{' '.join(allure_cmd)}")
    result = subprocess.run(
        allure_cmd, shell=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError(f"❌ Allure报告生成失败：{result.stderr}")

    # 校验生成结果
    single_report_file = html_dir / "index.html"
    if not single_report_file.exists():
        raise RuntimeError(f"❌ 单文件报告缺失：{single_report_file}")
    print(f"✅ Allure单文件报告生成完成：{single_report_file}")
    return single_report_file

if __name__ == "__main__":
    # 保留命令行执行能力
    if "--skip-test" in sys.argv:
        generate_allure_report(ALLURE_RESULTS, ALLURE_HTML)