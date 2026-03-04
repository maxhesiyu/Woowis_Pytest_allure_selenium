import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# 导入配置
from config.config import PROJECT_ROOT, TEST_LOGIN_PATH, TEST_SHOPPING_FreeGift_PATH, ALLURE_RESULTS, ALLURE_HTML
# 导入封装后的函数
from email_smtp.allure_html import generate_allure_report
from email_smtp.send_allure_email import clean_old_reports, zip_single_report, send_allure_email, get_zip_file_path


# ====================== 日志配置 ======================
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.config(state=tk.DISABLED)

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.config(state=tk.NORMAL)
        color = "black"
        if record.levelname == "INFO":
            color = "green"
        elif record.levelname == "WARNING":
            color = "orange"
        elif record.levelname == "ERROR":
            color = "red"
        self.text_widget.insert(tk.END, f"{msg}\n", color)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


def init_logger(text_widget):
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    text_handler = TextHandler(text_widget)
    formatter = logging.Formatter(
        "[%(levelname)s] [%(asctime)s] : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    text_handler.setFormatter(formatter)
    logger.addHandler(text_handler)

    text_widget.tag_configure("green", foreground="green")
    text_widget.tag_configure("orange", foreground="orange")
    text_widget.tag_configure("red", foreground="red")
    text_widget.tag_configure("black", foreground="black")

    return logger


# ====================== 核心执行函数（流水线模式） ======================
def run_pytest_test(test_file_path: Path, logger) -> int:
    """
    执行单个测试文件（仅执行一次）
    :param test_file_path: 测试文件路径
    :param logger: 日志器
    :return: pytest返回码（0=全部通过，非0=有失败）
    """
    logger.info(f"========== 开始执行测试：{test_file_path.name} ==========")
    # 清理历史结果（避免残留）
    clean_old_reports(ALLURE_RESULTS, ALLURE_HTML)

    # 构建pytest命令
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(test_file_path),
        "-v", "--tb=short",
        "--alluredir", str(ALLURE_RESULTS),
        "--clean-alluredir"
    ]
    logger.info(f"执行命令：{' '.join(pytest_cmd)}")

    # 执行测试
    process = subprocess.Popen(
        pytest_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT)
    )

    # 实时输出日志
    for line in iter(process.stdout.readline, ""):
        if line.strip():
            logger.info(line.strip())
    process.wait()

    retcode = process.returncode
    if retcode == 0:
        logger.info(f"✅ 测试执行完成：{test_file_path.name}（全部通过）")
    else:
        logger.warning(f"⚠️ 测试执行完成：{test_file_path.name}（部分失败，返回码：{retcode}）")
    return retcode


def run_test_pipeline(test_file_path: Path, logger, gen_allure: bool, send_email: bool):
    """
    测试执行流水线（一次测试 → 可选生成报告 → 可选发送邮件）
    :param test_file_path: 测试文件路径
    :param logger: 日志器
    :param gen_allure: 是否生成Allure HTML报告
    :param send_email: 是否发送邮件（依赖gen_allure=True）
    """
    try:
        # 1. 校验参数
        if send_email and not gen_allure:
            logger.warning("⚠️ 勾选了发送邮件但未勾选生成报告，自动开启生成报告")
            gen_allure = True

        # 2. 执行测试（仅执行一次）
        retcode = run_pytest_test(test_file_path, logger)
        test_status = "全部通过" if retcode == 0 else "部分失败"

        # 3. 可选生成Allure报告
        html_file = None
        if gen_allure:
            logger.info("========== 开始生成Allure报告 ==========")
            html_file = generate_allure_report(ALLURE_RESULTS, ALLURE_HTML)
            logger.info(f"✅ Allure报告生成完成：{html_file}")

        # 4. 可选发送邮件（依赖报告生成）
        if send_email and html_file:
            logger.info("========== 开始压缩并发送报告邮件 ==========")
            # 压缩报告
            zip_file = zip_single_report(html_file, get_zip_file_path())
            # 发送邮件
            send_allure_email(zip_file, test_status)
            logger.info("✅ 报告邮件发送完成")

        logger.info(
            f"\n🎉 流水线执行完成！测试文件：{test_file_path.name} | 生成报告：{gen_allure} | 发送邮件：{send_email}")

    except Exception as e:
        logger.error(f"❌ 流水线执行失败：{str(e)}", exc_info=True)
        messagebox.showerror("执行失败", f"测试流水线执行出错：{str(e)}")


# ====================== GUI按钮绑定函数 ======================
def run_login_test(logger, send_email_var: tk.BooleanVar, gen_allure_var: tk.BooleanVar):
    """运行登录测试（绑定GUI复选框状态）"""
    login_test_path = PROJECT_ROOT / "testcase/test_login.py"
    if not login_test_path.exists():
        logger.error(f"❌ 测试文件不存在：{login_test_path}")
        messagebox.showerror("错误", f"测试文件不存在：{login_test_path}")
        return

    # 获取复选框状态
    gen_allure = gen_allure_var.get()
    send_email = send_email_var.get()

    # 异步执行（避免界面卡死）
    def _run():
        run_test_pipeline(login_test_path, logger, gen_allure, send_email)

    threading.Thread(target=_run, daemon=True).start()


def run_shopping_test(logger, send_email_var: tk.BooleanVar, gen_allure_var: tk.BooleanVar):
    """运行赠品购物测试（绑定GUI复选框状态）"""
    shopping_test_path = PROJECT_ROOT / "testcase/test_shopping_freeGift.py"
    if not shopping_test_path.exists():
        logger.error(f"❌ 测试文件不存在：{shopping_test_path}")
        messagebox.showerror("错误", f"测试文件不存在：{shopping_test_path}")
        return

    # 获取复选框状态
    gen_allure = gen_allure_var.get()
    send_email = send_email_var.get()

    # 异步执行（避免界面卡死）
    def _run():
        run_test_pipeline(shopping_test_path, logger, gen_allure, send_email)

    threading.Thread(target=_run, daemon=True).start()


# ====================== 界面构建 ======================
def create_gui():
    root = tk.Tk()
    root.title("Woowis 自动化测试运行器")
    root.geometry("1000x700")
    root.resizable(True, True)

    # 1. 顶部配置区
    config_frame = ttk.LabelFrame(root, text="运行配置", padding=10)
    config_frame.pack(fill=tk.X, padx=10, pady=10)

    # 1.1 生成Allure报告复选框（全局变量，供按钮调用）
    var_gen_allure = tk.BooleanVar(value=True)
    cb_allure = ttk.Checkbutton(
        config_frame,
        text="运行完成后生成Allure HTML报告",
        variable=var_gen_allure
    )
    cb_allure.pack(anchor=tk.W, pady=2)

    # 1.2 发送邮件复选框（全局变量，供按钮调用）
    var_send_email = tk.BooleanVar(value=False)
    cb_email = ttk.Checkbutton(
        config_frame,
        text="生成报告后发送Allure报告邮件（需勾选上方生成报告）",
        variable=var_send_email
    )
    cb_email.pack(anchor=tk.W, pady=2)

    # 2. 按钮区
    btn_frame = ttk.Frame(root, padding=10)
    btn_frame.pack(fill=tk.X, padx=10, pady=5)

    # 2.1 运行登录测试按钮（传递复选框变量）
    btn_login = ttk.Button(
        btn_frame,
        text="运行登录测试 (test_login.py)",
        command=lambda: run_login_test(logger, var_send_email, var_gen_allure),
        width=40
    )
    btn_login.pack(side=tk.LEFT, padx=5, pady=5)

    # 2.2 运行赠品测试按钮（传递复选框变量）
    btn_shopping = ttk.Button(
        btn_frame,
        text="运行赠品购物测试 (test_shopping_freeGift.py)",
        command=lambda: run_shopping_test(logger, var_send_email, var_gen_allure),
        width=40
    )
    btn_shopping.pack(side=tk.LEFT, padx=5, pady=5)

    # 3. 日志输出区
    log_frame = ttk.LabelFrame(root, text="实时日志", padding=10)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 10))
    log_text.pack(fill=tk.BOTH, expand=True)

    # 初始化日志器
    global logger
    logger = init_logger(log_text)
    logger.info("✅ 测试运行器已初始化完成，可开始执行测试！")
    logger.info(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python路径：{sys.executable}")
    logger.info(f"项目根目录：{PROJECT_ROOT}\n")

    # 4. 底部状态栏
    status_var = tk.StringVar(value="就绪")
    status_bar = ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN)
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # 关闭事件
    def on_closing():
        if messagebox.askokcancel("退出", "确定要退出测试运行器吗？"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    # 检查必要文件
    required_files = [TEST_LOGIN_PATH, TEST_SHOPPING_FreeGift_PATH]
    missing_files = [str(f) for f in required_files if not f.exists()]
    if missing_files:
        print(f"⚠️ 缺失必要文件：{missing_files}")
        print(f"项目根目录：{PROJECT_ROOT}")
        sys.exit(1)
    # 启动GUI
    create_gui()