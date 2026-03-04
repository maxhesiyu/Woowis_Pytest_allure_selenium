import os
import sys
import shutil
import zipfile
import time
from pathlib import Path
from textwrap import dedent
import yagmail

# 导入配置
from config.config import EMAIL_CONFIG, ALLURE_HTML
from email_smtp.allure_html import generate_allure_report


# 压缩包命名
def get_zip_file_path() -> Path:
    """获取报告压缩包路径（带时间戳）"""
    email_dir = Path(__file__).parent
    return email_dir / f"测试报告_单文件_{time.strftime('%Y%m%d_%H%M%S')}.zip"

def zip_single_report(html_file: Path, zip_path: Path) -> Path:
    """
    压缩单文件Allure报告
    :param html_file: index.html文件路径
    :param zip_path: 压缩包输出路径
    :return: 压缩包路径
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=5) as zipf:
        zipf.write(html_file, arcname=html_file.name)  # 保留文件名，解压后可直接打开
    file_size = os.path.getsize(zip_path) / 1024 / 1024
    print(f"✅ 报告压缩完成：{zip_path}（大小：{file_size:.2f}MB）")
    return zip_path

def send_allure_email(zip_file: Path, test_status: str = "未知") -> None:
    """
    发送包含压缩报告的邮件
    :param zip_file: 报告压缩包路径
    :param test_status: 测试结果状态（全部通过/部分失败）
    """
    subject = f"【自动化测试报告_单文件】{test_status} {time.strftime('%Y%m%d_%H%M%S')}"
    body = dedent("""
    <html>
      <body>
        <p>您好！</p>
        <p>附件为本次自动化测试的Allure单文件报告（ZIP压缩包），打开方式：</p>
        <ol>
          <li>解压ZIP包，得到「index.html」文件；</li>
          <li>直接双击「index.html」（推荐Chrome/Firefox浏览器），无需执行任何命令；</li>
        </ol>
        <p>测试结果：{test_status}。</p>
      </body>
    </html>
    """).format(test_status=test_status)

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
            attachments=[str(zip_file)]
        )
        yag.close()
        print("✅ 测试报告邮件发送成功！")
    except Exception as e:
        raise RuntimeError(f"❌ 邮件发送失败：{str(e)}")

def clean_old_reports(results_dir: Path, html_dir: Path) -> None:
    """清理历史报告（结果目录、HTML目录、压缩包）"""
    # 清理结果目录和HTML目录
    for dir_path in [results_dir, html_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
            dir_path.mkdir(parents=True, exist_ok=True)
    # 清理历史压缩包
    email_dir = Path(__file__).parent
    for zip_file in email_dir.glob("测试报告_单文件_*.zip"):
        zip_file.unlink(missing_ok=True)
    print("✅ 历史报告清理完成")

if __name__ == "__main__":
    # 保留基础命令行能力（仅用于测试）
    from config.config import ALLURE_RESULTS
    clean_old_reports(ALLURE_RESULTS, ALLURE_HTML)
    html_file = generate_allure_report(ALLURE_RESULTS, ALLURE_HTML)
    zip_file = zip_single_report(html_file, get_zip_file_path())
    send_allure_email(zip_file, "测试")