import os
import sys
import shutil
import subprocess
import yagmail
import zipfile
import time
from pathlib import Path
from textwrap import dedent

# ========== 路径配置 ==========
EMAIL_DIR = Path(__file__).absolute().parent
PROJECT_ROOT = EMAIL_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# 导入配置（确保config.py中定义了以下路径）
from config.config import TEST_CASE_DIR, ALLURE_RESULTS, ALLURE_HTML, EMAIL_CONFIG

# 单文件报告压缩包命名（简化，因为只有一个index.html）
ALLURE_ZIP_FILE = EMAIL_DIR / f"测试报告_单文件_{time.strftime('%Y%m%d_%H%M%S')}.zip"


# ========== 清理历史报告 ==========
def clean_old_report():
    for dir_path in [ALLURE_RESULTS, ALLURE_HTML]:
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
    for zip_file in EMAIL_DIR.glob("测试报告_单文件_*.zip"):
        zip_file.unlink(missing_ok=True)
    print("✅ 历史报告清理完成")


# ========== 执行测试用例 ==========
def run_pytest():
    pytest_exe = str(PROJECT_ROOT / ".venv" / "Scripts" / "pytest.exe")
    pytest_cmd = [
        pytest_exe, str(TEST_CASE_DIR), "-v",
        "--alluredir", str(ALLURE_RESULTS), "--clean-alluredir"
    ]
    print(f"📝 执行命令：{' '.join(pytest_cmd)}")

    result = subprocess.run(
        pytest_cmd, shell=False, text=True, encoding="utf-8", check=False
    )

    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
    result_files = list(ALLURE_RESULTS.glob("*.json"))
    if len(result_files) == 0:
        raise RuntimeError(
            f"❌ pytest执行失败：allure-results无测试结果，返回码{result.returncode}\n"
            f"💡 解决方案：\n1. 执行：.venv\\Scripts\\pip install allure-pytest==2.20.0\n2. 重新激活虚拟环境"
        )
    print(f"✅ pytest执行完成（返回码：{result.returncode}，生成{len(result_files)}个测试结果文件）")
    return result.returncode


# ========== 生成单文件Allure报告+压缩（核心适配） ==========
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


    # 3. 压缩单文件报告（仅压缩index.html，简化逻辑）
    def zip_single_report(file_path, zip_path):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=5) as zipf:
            # 压缩时保留文件名，解压后直接双击即可
            zipf.write(file_path, arcname=file_path.name)

    zip_single_report(single_report_file, ALLURE_ZIP_FILE)
    print(f"✅ 单文件报告压缩完成：{ALLURE_ZIP_FILE}（压缩后大小：{os.path.getsize(ALLURE_ZIP_FILE) / 1024 / 1024:.2f}MB）")


# ========== 发送邮件（适配单文件打开方式） ==========
def send_email(retcode=0):
    status = "全部通过" if retcode == 0 else "部分失败"
    subject = f"【自动化测试报告_单文件】{status} {time.strftime('%Y%m%d_%H%M%S')}"

    # 单文件报告可直接双击打开，无需allure open命令
    body = dedent("""
    <html>
      <body>
        <p>您好！</p>
        <p>附件为本次自动化测试的Allure单文件报告（ZIP压缩包），打开方式：</p>
        <ol>
          <li>解压ZIP包，得到「index.html」文件；</li>
          <li>直接双击「index.html」（推荐Chrome/Firefox浏览器），无需执行任何命令；</li>
        </ol>
        <p>测试结果：{status}。</p>
      </body>
    </html>
    """).format(status=status)

    try:
        yag = yagmail.SMTP(
            user=EMAIL_CONFIG["sender"],
            password=EMAIL_CONFIG["password"],
            host=EMAIL_CONFIG["host"],
            port=EMAIL_CONFIG["port"],
            smtp_ssl=True,
            timeout=30
        )
        yag.send(
            to=EMAIL_CONFIG["receivers"],
            subject=subject,
            contents=body,
            attachments=[str(ALLURE_ZIP_FILE)]
        )
        yag.close()
        print("✅ 邮件发送成功！")
    except Exception as e:
        raise RuntimeError(f"❌ 邮件发送失败：{str(e)}")


# ========== 主流程 ==========
def main():
    try:
        clean_old_report()
        retcode = run_pytest()
        generate_allure_report()
        send_email(retcode)
        status = "全部通过" if retcode == 0 else "部分失败"
        print(f"\n🎉 全流程完成！测试{status}，文件报告已发送至指定邮箱")
    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        raise


if __name__ == "__main__":
    main()