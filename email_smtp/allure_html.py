import os
import sys
import shutil
import subprocess
import zipfile
import time
from pathlib import Path
from textwrap import dedent

# ========== 核心路径配置（移除邮件相关路径） ==========
# 获取当前脚本所在目录
SCRIPT_DIR = Path(__file__).absolute().parent
# 项目根目录（当前脚本的上级目录）
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# 导入配置
from config.config import TEST_CASE_DIR, ALLURE_RESULTS, ALLURE_HTML

# 单文件报告压缩包命名（可选保留，便于归档）
ALLURE_ZIP_FILE = SCRIPT_DIR / f"Allure测试报告_{time.strftime('%Y%m%d_%H%M%S')}.zip"


# ========== 1. 清理历史报告（避免残留影响） ==========
def clean_old_report():
    """清理历史的allure结果、报告、压缩包"""
    # 清理allure结果和报告目录
    for dir_path in [ALLURE_RESULTS, ALLURE_HTML]:
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
            print(f"🗑️  已清理历史目录：{dir_path}")
    # 清理旧的报告压缩包
    for zip_file in SCRIPT_DIR.glob("Allure测试报告_*.zip"):
        zip_file.unlink(missing_ok=True)
    print("✅ 历史报告清理完成\n")


# ========== 2. 执行pytest用例（生成allure原始结果） ==========
def run_pytest():
    """执行pytest用例，生成allure-results原始数据"""
    # 拼接pytest执行路径（虚拟环境中的pytest）
    pytest_exe = str(PROJECT_ROOT / ".venv" / "Scripts" / "pytest.exe")
    # 构建pytest执行命令
    pytest_cmd = [
        pytest_exe, str(TEST_CASE_DIR), "-v",  # 执行指定目录的用例，显示详细日志
        "--alluredir", str(ALLURE_RESULTS),    # 生成allure原始结果的目录
        "--clean-alluredir"                    # 每次执行前清空allure-results
    ]
    print(f"📝 开始执行pytest用例，命令：{' '.join(pytest_cmd)}")

    # 执行pytest命令
    result = subprocess.run(
        pytest_cmd, shell=False, text=True, encoding="utf-8", check=False
    )

    # 确保allure-results目录存在，并校验结果文件
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
    result_files = list(ALLURE_RESULTS.glob("*.json"))  # allure结果文件为json格式

    # 校验：如果没有生成结果文件，说明用例执行失败
    if len(result_files) == 0:
        raise RuntimeError(
            f"❌ pytest执行失败：allure-results目录无测试结果文件！\n"
            f"返回码：{result.returncode}\n"
            f"💡 排查方案：\n1. 检查虚拟环境：.venv\\Scripts\\activate\n2. 安装依赖：pip install allure-pytest==2.20.0\n3. 确认测试用例路径正确：{TEST_CASE_DIR}"
        )

    print(f"✅ pytest用例执行完成！\n"
          f"返回码：{result.returncode}（0=全部通过，非0=有失败/错误）\n"
          f"生成Allure原始结果文件数：{len(result_files)}个\n")
    return result.returncode


# ========== 3. 生成Allure单文件报告（核心功能） ==========
def generate_allure_report():
    result_files = list(ALLURE_RESULTS.glob("*.json"))
    if len(result_files) == 0:
        raise RuntimeError("❌ allure-results无测试结果，无法生成报告")

    # 1. 生成单文件报告（--single-file是核心参数）
    allure_gen_cmd = [
        "allure", "generate", str(ALLURE_RESULTS),
        "-o", str(ALLURE_HTML), "--clean", "--single-file"  # 单文件核心参数
    ]
    allure_result = subprocess.run(
        allure_gen_cmd, shell=True, text=True, encoding="utf-8", capture_output=True
    )
    if allure_result.returncode != 0:
        raise RuntimeError(
            f"❌ Allure单文件报告生成失败：{allure_result.stderr}\n"
            f"💡 排查步骤：\n1. 确认Allure CLI版本≥2.20.0（allure --version）\n2. 重新执行allure generate命令"
        )
    print(f"✅ Allure单文件报告生成完成：{ALLURE_HTML}")

    # 2. 校验单文件报告完整性（仅需检查index.html是否存在）
    single_report_file = ALLURE_HTML / "index.html"
    if not single_report_file.exists():
        raise RuntimeError(f"❌ 单文件报告缺失：{single_report_file}，生成失败")
    print(f"✅ 单文件报告校验通过（文件存在）")



# ========== 主执行流程（串联所有步骤） ==========
def main():
    """主流程：清理历史 → 执行用例 → 生成报告"""
    try:
        # 步骤1：清理历史报告
        clean_old_report()
        # 步骤2：执行pytest用例
        retcode = run_pytest()
        # 步骤3：生成Allure单文件报告
        generate_allure_report()

        # 最终结果汇总
        status = "✅ 所有用例执行通过" if retcode == 0 else "⚠️  部分用例执行失败/出错"
        print(f"🎉 全流程执行完成！\n{status}\n"
              f"📌 报告文件位置：\n"
              f"1. 单文件HTML报告：{ALLURE_HTML / 'index.html'}\n"
              f"2. 压缩包报告：{ALLURE_ZIP_FILE}")

    except Exception as e:
        print(f"\n❌ 执行失败：{str(e)}")
        # 抛出异常，让脚本返回非0退出码（便于CI/CD判断结果）
        raise


if __name__ == "__main__":
    # 启动主流程
    main()