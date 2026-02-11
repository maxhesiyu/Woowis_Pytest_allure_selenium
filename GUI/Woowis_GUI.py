import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QTextEdit, QGroupBox, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# ========== 路径配置（适配项目结构） ==========
GUI_DIR = Path(__file__).absolute().parent
PROJECT_ROOT = GUI_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# 导入项目核心模块（修正：直接引用全局变量，而非ENV类属性）
from config.config import (
    LOG_DIR, PROJECT_ROOT, ENV,
    ALLURE_RESULTS, ALLURE_HTML  # 直接导入全局的allure路径
)
from email_smtp.send_allure_email import (
    clean_old_report, run_pytest, generate_allure_report, send_email
)
from common.log import log

# ========== 日志重定向Handler（输出到GUI日志栏） ==========
class GuiLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        # 日志格式（对齐原log.py的格式）
        self.formatter = logging.Formatter(
            '[%(levelname)s] [%(asctime)s.%(msecs)03d] : %(message)s -> %(funcName)s line:%(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def emit(self, record):
        # 线程安全的日志输出
        msg = self.format(record)
        self.text_widget.append(msg)
        # 自动滚动到最新日志
        self.text_widget.verticalScrollBar().setValue(
            self.text_widget.verticalScrollBar().maximum()
        )

# ========== 测试执行线程（避免界面卡死） ==========
class TestRunnerThread(QThread):
    # 定义信号：日志输出、执行完成
    log_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(bool, str)

    def __init__(self, gen_allure: bool, send_email_flag: bool):
        super().__init__()
        self.gen_allure = gen_allure
        self.send_email_flag = send_email_flag

    def run(self):
        try:
            # 步骤1：清理历史报告
            self.log_signal.emit("🔍 开始清理历史报告...")
            clean_old_report()
            self.log_signal.emit("✅ 历史报告清理完成")

            # 步骤2：执行pytest测试用例
            self.log_signal.emit("📝 开始执行pytest测试用例...")
            retcode = run_pytest()
            self.log_signal.emit(f"✅ pytest执行完成（返回码：{retcode}）")

            # 步骤3：生成Allure报告（按需）
            if self.gen_allure:
                self.log_signal.emit("📊 开始生成Allure单文件报告...")
                generate_allure_report()
                self.log_signal.emit("✅ Allure报告生成完成")
            else:
                self.log_signal.emit("ℹ️ 跳过Allure报告生成（未勾选）")

            # 步骤4：发送邮件报告（按需）
            if self.send_email_flag:
                if self.gen_allure:
                    self.log_signal.emit("📧 开始发送邮件报告...")
                    send_email(retcode)
                    self.log_signal.emit("✅ 邮件报告发送完成")
                else:
                    self.log_signal.emit("❌ 发送邮件需先生成Allure报告，跳过邮件发送")
            else:
                self.log_signal.emit("ℹ️ 跳过邮件报告发送（未勾选）")

            # 执行完成
            status = "全部通过" if retcode == 0 else "部分失败"
            self.log_signal.emit(f"\n🎉 测试执行完成！测试结果：{status}")
            self.finish_signal.emit(True, f"执行成功：{status}")

        except Exception as e:
            error_msg = f"❌ 执行失败：{str(e)}"
            self.log_signal.emit(error_msg)
            self.finish_signal.emit(False, error_msg)

# ========== 主GUI窗口 ==========
class RunnerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_log_handler()
        self.run_thread = None  # 测试执行线程

    def init_ui(self):
        # 窗口基础设置
        self.setWindowTitle("自动化测试执行器（Python3.13+PyQt6）")
        self.setMinimumSize(800, 600)
        self.setFont(QFont("Microsoft YaHei", 9))

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== 1. 功能配置区 ==========
        config_group = QGroupBox("测试配置")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # 复选框：生成Allure报告
        self.chk_allure = QCheckBox("生成Allure单文件测试报告")
        self.chk_allure.setChecked(True)  # 默认勾选
        self.chk_allure.setFont(QFont("Microsoft YaHei", 10))
        config_layout.addWidget(self.chk_allure)

        # 复选框：发送邮件报告
        self.chk_email = QCheckBox("发送Allure报告至指定邮箱")
        self.chk_email.setChecked(True)  # 默认勾选
        self.chk_email.setFont(QFont("Microsoft YaHei", 10))
        config_layout.addWidget(self.chk_email)

        # 执行按钮
        self.btn_run = QPushButton("开始执行测试")
        self.btn_run.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn_run.clicked.connect(self.start_test)
        config_layout.addWidget(self.btn_run, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(config_group)

        # ========== 2. 日志输出区 ==========
        log_group = QGroupBox("实时日志")
        log_layout = QVBoxLayout(log_group)

        # 日志文本框（核心修改：黑色底色+白色文字）
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #000000;  /* 黑色底色 */
                color: #ffffff;             /* 白色文字，保证可读性 */
                border: 1px solid #333333;  /* 深色边框，适配黑色背景 */
                border-radius: 5px;
                padding: 10px;
            }
            /* 可选：选中文字时的背景色，适配黑色主题 */
            QTextEdit::selection {
                background-color: #444444;
                color: #ffffff;
            }
        """)
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_group, stretch=1)  # 日志栏占主要空间

    def init_log_handler(self):
        # 新增GUI日志处理器，整合原有日志
        gui_handler = GuiLogHandler(self.log_text)
        log.addHandler(gui_handler)
        # 输出初始化日志
        log.info("📌 自动化测试执行器已初始化完成")
        log.info(f"🔧 项目根目录：{PROJECT_ROOT}")
        log.info(f"🌐 测试环境地址：{ENV.URL}")
        log.info(f"📁 Allure报告目录：{ALLURE_HTML}")

    def start_test(self):
        # 禁用按钮，防止重复点击
        self.btn_run.setDisabled(True)
        self.log_text.clear()

        # 获取复选框状态
        gen_allure = self.chk_allure.isChecked()
        send_email_flag = self.chk_email.isChecked()

        # 创建并启动测试线程
        self.run_thread = TestRunnerThread(gen_allure, send_email_flag)
        self.run_thread.log_signal.connect(lambda msg: log.info(msg))  # 日志转发到GUI
        self.run_thread.finish_signal.connect(self.on_test_finish)
        self.run_thread.start()

    def on_test_finish(self, success: bool, msg: str):
        # 恢复按钮状态
        self.btn_run.setDisabled(False)
        # 输出最终结果
        if success:
            log.info(msg)
        else:
            log.error(msg)

# ========== 程序入口 ==========
if __name__ == "__main__":
    # 确保必要目录存在（修正：直接使用全局变量，而非ENV类属性）
    for dir_path in [LOG_DIR, ALLURE_RESULTS, ALLURE_HTML]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # PyQt6应用初始化
    app = QApplication(sys.argv)
    window = RunnerWindow()
    window.show()
    sys.exit(app.exec())