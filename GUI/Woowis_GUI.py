import sys
import logging
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QTextEdit, QGroupBox, QLabel, QSizePolicy,
    QLineEdit, QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from PyQt6.QtGui import QFont

# ========== 路径配置（适配项目结构） ==========
GUI_DIR = Path(__file__).absolute().parent
PROJECT_ROOT = GUI_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# 导入项目核心模块
from config.config import (
    LOG_DIR, PROJECT_ROOT, ENV, TEST_CASE_DIR,
    ALLURE_RESULTS, ALLURE_HTML
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
        # 对齐log.py的日志格式
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


# ========== 登录测试执行线程（适配原有无参run_pytest） ==========
class LoginTestRunnerThread(QThread):
    # 定义信号：日志输出、执行完成
    log_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(bool, str)

    def __init__(self, gen_allure: bool, send_email_flag: bool,
                 test_case_filter: str, pcno_filter: str):
        super().__init__()
        self.gen_allure = gen_allure
        self.send_email_flag = send_email_flag
        self.test_case_filter = test_case_filter  # 用例筛选（如test_login）
        self.pcno_filter = pcno_filter  # 账号筛选

    def run(self):
        try:
            # 步骤1：清理历史报告
            self.log_signal.emit("🔍 开始清理历史Allure报告...")
            clean_old_report()
            self.log_signal.emit("✅ 历史报告清理完成")

            # 步骤2：设置筛选条件（核心适配：通过环境变量传递筛选参数）
            self.log_signal.emit("📝 配置登录测试筛选条件...")

            # 1. 覆盖测试用例目录（仅执行test_login.py）
            os.environ["TEST_CASE_TARGET"] = str(PROJECT_ROOT / "testcase/test_login.py")
            self.log_signal.emit(f"🔍 测试用例路径已指定：{os.environ['TEST_CASE_TARGET']}")

            # 2. 设置用例筛选（pytest -k 参数）
            if self.test_case_filter:
                os.environ["PYTEST_K_FILTER"] = self.test_case_filter
                self.log_signal.emit(f"🔍 筛选执行用例：{self.test_case_filter}")

            # 3. 设置账号筛选（供test_login.py读取）
            if self.pcno_filter:
                os.environ["TEST_PCNO_FILTER"] = self.pcno_filter
                self.log_signal.emit(f"🔍 筛选执行账号：{self.pcno_filter}")

            # 步骤3：执行pytest测试用例（适配原有无参run_pytest）
            self.log_signal.emit("🚀 开始执行登录测试用例...")
            # 临时修改send_allure_email.py中run_pytest的执行路径和筛选逻辑
            retcode = self.custom_run_pytest()  # 替换原run_pytest调用
            self.log_signal.emit(f"✅ 登录测试执行完成（返回码：{retcode}）")

            # 步骤4：生成Allure报告（按需）
            if self.gen_allure:
                self.log_signal.emit("📊 开始生成Allure登录测试报告...")
                generate_allure_report()
                self.log_signal.emit(f"✅ Allure报告已生成至：{ALLURE_HTML}")
            else:
                self.log_signal.emit("ℹ️ 跳过Allure报告生成（未勾选）")

            # 步骤5：发送邮件报告（按需）
            if self.send_email_flag:
                if self.gen_allure:
                    self.log_signal.emit("📧 开始发送登录测试报告邮件...")
                    send_email(retcode)
                    self.log_signal.emit("✅ 邮件报告发送完成")
                else:
                    self.log_signal.emit("❌ 发送邮件需先生成Allure报告，跳过邮件发送")
            else:
                self.log_signal.emit("ℹ️ 跳过邮件报告发送（未勾选）")

            # 执行完成
            status = "全部通过" if retcode == 0 else "部分失败/异常"
            self.log_signal.emit(f"\n🎉 登录测试执行完成！测试结果：{status}")
            self.finish_signal.emit(True, f"执行成功：{status}")

        except Exception as e:
            error_msg = f"❌ 登录测试执行失败：{str(e)}"
            self.log_signal.emit(error_msg)
            self.finish_signal.emit(False, error_msg)
        finally:
            # 清理环境变量
            for key in ["TEST_CASE_TARGET", "PYTEST_K_FILTER", "TEST_PCNO_FILTER"]:
                if key in os.environ:
                    del os.environ[key]

    def custom_run_pytest(self):
        """自定义pytest执行逻辑（适配原有无参run_pytest，支持筛选）"""
        import subprocess
        # 拼接pytest执行路径（虚拟环境中的pytest）
        pytest_exe = str(PROJECT_ROOT / ".venv" / "Scripts" / "pytest.exe")
        # 构建pytest执行命令
        pytest_cmd = [
            pytest_exe,
            os.environ.get("TEST_CASE_TARGET", str(TEST_CASE_DIR)),  # 优先用指定的用例文件
            "-v",  # 显示详细日志
            "--alluredir", str(ALLURE_RESULTS),  # 生成allure原始结果的目录
            "--clean-alluredir"  # 每次执行前清空allure-results
        ]
        # 添加用例筛选（-k参数）
        if "PYTEST_K_FILTER" in os.environ:
            pytest_cmd.extend(["-k", os.environ["PYTEST_K_FILTER"]])

        self.log_signal.emit(f"📝 执行pytest命令：{' '.join(pytest_cmd)}")

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
                f"💡 排查方案：\n1. 检查虚拟环境：.venv\\Scripts\\activate\n2. 安装依赖：pip install allure-pytest==2.20.0\n3. 确认测试用例路径正确：{os.environ.get('TEST_CASE_TARGET', str(TEST_CASE_DIR))}"
            )

        self.log_signal.emit(f"✅ pytest用例执行完成！\n"
                             f"返回码：{result.returncode}（0=全部通过，非0=有失败/错误）\n"
                             f"生成Allure原始结果文件数：{len(result_files)}个\n")
        return result.returncode


# ========== 主GUI窗口（适配登录测试） ==========
class LoginTestRunnerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_log_handler()
        self.run_thread = None  # 测试执行线程

    def init_ui(self):
        # 窗口基础设置
        self.setWindowTitle("多特瑞 - 登录自动化测试执行器")
        self.setMinimumSize(900, 700)
        self.setFont(QFont("Microsoft YaHei", 9))

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== 1. 登录测试专属配置区 ==========
        login_config_group = QGroupBox("登录测试专属配置")
        login_config_layout = QGridLayout(login_config_group)
        login_config_layout.setSpacing(12)
        login_config_layout.setContentsMargins(15, 15, 15, 15)

        # 用例筛选
        login_config_layout.addWidget(QLabel("测试用例筛选："), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.case_combo = QComboBox()
        self.case_combo.addItems(["", "test_login"])
        self.case_combo.setPlaceholderText("留空执行所有登录用例")
        self.case_combo.setFont(QFont("Microsoft YaHei", 9))
        login_config_layout.addWidget(self.case_combo, 0, 1)

        # 环境显示
        login_config_layout.addWidget(QLabel("测试环境："), 2, 0, Qt.AlignmentFlag.AlignRight)
        env_label = QLabel(ENV.URL)
        env_label.setFont(QFont("Microsoft YaHei", 9))
        env_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        login_config_layout.addWidget(env_label, 2, 1)

        main_layout.addWidget(login_config_group)

        # ========== 2. 通用配置区 ==========
        common_config_group = QGroupBox("通用配置")
        common_config_layout = QVBoxLayout(common_config_group)
        common_config_layout.setSpacing(10)

        # 复选框：生成Allure报告
        self.chk_allure = QCheckBox("生成Allure单文件测试报告")
        self.chk_allure.setChecked(True)
        self.chk_allure.setFont(QFont("Microsoft YaHei", 10))
        common_config_layout.addWidget(self.chk_allure)

        # 复选框：发送邮件报告
        self.chk_email = QCheckBox("发送Allure报告至指定邮箱")
        self.chk_email.setChecked(True)
        self.chk_email.setFont(QFont("Microsoft YaHei", 10))
        common_config_layout.addWidget(self.chk_email)

        # 执行按钮
        self.btn_run = QPushButton("开始执行登录测试")
        self.btn_run.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn_run.clicked.connect(self.start_login_test)
        common_config_layout.addWidget(self.btn_run, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(common_config_group)

        # ========== 3. 日志输出区 ==========
        log_group = QGroupBox("实时日志（登录测试）")
        log_layout = QVBoxLayout(log_group)

        # 日志文本框（黑色主题）
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 12px;
                line-height: 1.4;
            }
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
        log.info("📌 登录自动化测试执行器已初始化完成")
        log.info(f"🔧 项目根目录：{PROJECT_ROOT}")
        log.info(f"🌐 测试环境地址：{ENV.URL}")
        log.info(f"📁 Allure报告目录：{ALLURE_HTML}")
        log.info("💡 提示：可通过「测试账号筛选」输入PCNO仅执行指定账号的登录测试")

    def start_login_test(self):
        # 禁用按钮，防止重复点击
        self.btn_run.setDisabled(True)
        self.log_text.clear()

        # 获取配置项
        gen_allure = self.chk_allure.isChecked()
        send_email_flag = self.chk_email.isChecked()
        test_case_filter = self.case_combo.currentText().strip()
        pcno_filter = self.pcno_input.text().strip()

        # 日志输出配置信息
        log.info("🔧 开始执行登录测试，配置如下：")
        log.info(f"   - 用例筛选：{test_case_filter or '所有登录用例'}")
        log.info(f"   - 账号筛选：{pcno_filter or '所有账号'}")
        log.info(f"   - 生成Allure报告：{gen_allure}")
        log.info(f"   - 发送邮件报告：{send_email_flag}")

        # 创建并启动测试线程
        self.run_thread = LoginTestRunnerThread(
            gen_allure, send_email_flag, test_case_filter, pcno_filter
        )
        self.run_thread.log_signal.connect(lambda msg: log.info(msg))
        self.run_thread.finish_signal.connect(self.on_test_finish)
        self.run_thread.start()

    def on_test_finish(self, success: bool, msg: str):
        # 恢复按钮状态
        self.btn_run.setDisabled(False)
        # 输出最终结果
        if success:
            log.info(f"🏁 {msg}")
        else:
            log.error(f"💥 {msg}")


# ========== 程序入口 ==========
if __name__ == "__main__":
    # 确保必要目录存在
    for dir_path in [LOG_DIR, ALLURE_RESULTS, ALLURE_HTML]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # PyQt6应用初始化
    app = QApplication(sys.argv)
    # 设置应用风格
    app.setStyle("Fusion")
    window = LoginTestRunnerWindow()
    window.show()
    sys.exit(app.exec())