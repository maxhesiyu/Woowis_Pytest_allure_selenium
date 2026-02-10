import sys
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

# ========== 路径配置 ==========
SCRIPT_DIR = Path(__file__).absolute().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.append(str(PROJECT_ROOT))
from config.config import ALLURE_HTML

PDF_FILE = SCRIPT_DIR / f"Allure测试报告_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
LOCAL_CHROMIUM_PATH = "C:\\Users\\28477\\AppData\\Local\\ms-playwright\\chromium-1208\\chrome-win64\\chrome.exe"


def check_allure_html():
    html_path = ALLURE_HTML / "index.html"
    if not html_path.exists():
        raise RuntimeError(f"❌ 未找到Allure报告：{html_path}")
    print(f"✅ 检测到Allure报告：{html_path}")
    return html_path


def convert_html_to_pdf(html_file: Path, pdf_file: Path):
    if not Path(LOCAL_CHROMIUM_PATH).exists():
        raise RuntimeError(f"❌ Chromium未找到：{LOCAL_CHROMIUM_PATH}")
    print(f"✅ 检测到本地Chromium：{LOCAL_CHROMIUM_PATH}")
    print(f"\n📱 启动浏览器渲染Allure报告（全屏模式）...")

    with sync_playwright() as p:
        # 关键修改1：设置超大视口（4K分辨率）+ 禁用移动端模式
        browser = p.chromium.launch(
            headless=True,
            executable_path=LOCAL_CHROMIUM_PATH,
            args=["--no-sandbox", "--start-maximized"]  # 启动时最大化窗口
        )
        context = browser.new_context(
            viewport={"width": 3840, "height": 2160},  # 4K视口，覆盖所有宽屏内容
            is_mobile=False,  # 强制桌面端渲染
            device_scale_factor=1.0  # 缩放比例1:1
        )
        page = context.new_page()

        # 加载页面（延长等待时间，确保JS完全渲染）
        html_url = f"file:///{html_file.absolute().as_posix().replace('\\', '/')}"
        page.goto(html_url, wait_until="networkidle", timeout=120000)

        # 关键修改2：强制滚动到页面底部，触发懒加载内容渲染
        print("🔄 滚动页面，加载所有懒加载内容...")
        page.evaluate("""() => {
            // 滚动到底部，触发Allure的懒加载
            window.scrollTo(0, document.body.scrollHeight);
            // 等待5秒，让所有内容渲染完成
            return new Promise(resolve => setTimeout(resolve, 5000));
        }""")
        time.sleep(2)  # 额外等待，确保渲染完成

        # 关键修改3：PDF导出参数（自适应尺寸+缩放+无边距）
        page.pdf(
            path=str(pdf_file),
            # 替代A4固定尺寸：按页面实际宽度/高度导出（避免裁剪）
            width="3840px",
            height="2160px",
            print_background=True,  # 保留背景/图表
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},  # 无边距
            scale=1.0,  # 缩放比例（1.0=100%，可调整为0.8适配打印）
            prefer_css_page_size=True  # 优先使用CSS定义的页面尺寸
        )

        browser.close()

    if not pdf_file.exists():
        raise RuntimeError(f"❌ PDF未生成：{pdf_file}")
    print(f"✅ PDF转换成功（完整内容）！\n📌 文件路径：{pdf_file}")
    return pdf_file


def main():
    try:
        html_file = check_allure_html()
        convert_html_to_pdf(html_file, PDF_FILE)
        print(f"\n🎉 转换完成！PDF已完整包含所有内容：\n{PDF_FILE}")
    except Exception as e:
        print(f"\n❌ 转换失败：{str(e)}")
        raise


if __name__ == "__main__":
    if sys.platform == "win32":
        subprocess.run("chcp 65001", shell=True, check=False)
    main()