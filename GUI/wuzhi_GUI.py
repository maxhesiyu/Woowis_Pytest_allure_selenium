# -*- coding: utf-8 -*-
import sys
import traceback
import time
import subprocess
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

# ========== 1. 仅检查用例文件是否存在（无需导入类） ==========
def check_case_file_exists():
    """检查用例文件是否存在，避免执行时找不到文件"""
    login_case_path = r"D:\pythonProject\Pytest_allure_2\testtcase\test_login.py"
    promo_case_path = r"D:\pythonProject\Pytest_allure_2\testtcase\test_shopping_FreeGift.py"
    exists = True
    error_msg = ""
    if not os.path.exists(login_case_path):
        exists = False
        error_msg += f"登录用例文件不存在：{login_case_path}\n"
    if not os.path.exists(promo_case_path):
        exists = False
        error_msg += f"促销用例文件不存在：{promo_case_path}\n"
    return exists, error_msg

# ========== 用例运行线程类（统一用subprocess调用所有脚本/用例） ==========
class CaseThread(QThread):
    log_signal = Signal(str)
    finish_signal = Signal()

    def __init__(self, case_type):
        super().__init__()
        self.case_type = case_type
        # 定义各脚本/用例的路径
        self.paths = {
            "login": r"D:\pythonProject\Pytest_allure_2\testtcase\test_login.py::TestLogin::test_login",
            "promo": r"D:\pythonProject\Pytest_allure_2\testtcase\test_shopping_FreeGift.py::TestFreeGift::test_shopping_FreeGift",
            "report": r"D:\pythonProject\Pytest_allure_2\email_smtp\allure_html.py"
        }
        # 获取虚拟环境的Python解释器和pytest路径
        self.python_exe = sys.executable
        self.pytest_exe = os.path.join(os.path.dirname(self.python_exe), "Scripts", "pytest.exe")
        # 若pytest.exe不存在（比如Linux/Mac），直接用python -m pytest
        if not os.path.exists(self.pytest_exe):
            self.pytest_exe = f"{self.python_exe} -m pytest"

    def run(self):
        try:
            if self.case_type == "login":
                self.log_signal.emit("========== 开始执行登录用例（Pytest命令行模式） ==========")
                # 检查用例文件是否存在
                case_exists, error_msg = check_case_file_exists()
                if not case_exists:
                    self.log_signal.emit(f"❌ 前置错误：{error_msg}")
                    return

                # 构造Pytest命令行
                if os.path.exists(self.pytest_exe):
                    # Windows下直接调用pytest.exe
                    cmd = [
                        self.pytest_exe,
                        self.paths["login"],
                        "-v", "-s", "--tb=short", "--no-header", "--no-summary"
                    ]
                else:
                    # 通用方式：python -m pytest
                    cmd = [
                        self.python_exe, "-m", "pytest",
                        self.paths["login"],
                        "-v", "-s", "--tb=short", "--no-header", "--no-summary"
                    ]

                self.log_signal.emit(f"📌 执行Pytest命令：{' '.join(cmd)}")
                # 执行Pytest并捕获输出
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    timeout=300,  # 5分钟超时
                    cwd=os.path.dirname(self.python_exe)  # 切换到虚拟环境目录，确保依赖正确
                )

                # 输出执行结果
                if result.stdout:
                    self.log_signal.emit(f"📝 Pytest输出：\n{result.stdout}")
                if result.stderr:
                    self.log_signal.emit(f"⚠️ Pytest错误输出：\n{result.stderr}")
                if result.returncode == 0:
                    self.log_signal.emit("✅ 登录用例执行成功！")
                else:
                    self.log_signal.emit(f"❌ 登录用例执行失败（返回码：{result.returncode}）")

            elif self.case_type == "promo":
                self.log_signal.emit("========== 开始执行促销用例（Pytest命令行模式） ==========")
                case_exists, error_msg = check_case_file_exists()
                if not case_exists:
                    self.log_signal.emit(f"❌ 前置错误：{error_msg}")
                    return

                # 构造Pytest命令行
                if os.path.exists(self.pytest_exe):
                    cmd = [self.pytest_exe, self.paths["promo"], "-v", "-s", "--tb=short", "--no-header", "--no-summary"]
                else:
                    cmd = [self.python_exe, "-m", "pytest", self.paths["promo"], "-v", "-s", "--tb=short", "--no-header", "--no-summary"]

                self.log_signal.emit(f"📌 执行Pytest命令：{' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    timeout=300,
                    cwd=os.path.dirname(self.python_exe)
                )

                if result.stdout:
                    self.log_signal.emit(f"📝 Pytest输出：\n{result.stdout}")
                if result.stderr:
                    self.log_signal.emit(f"⚠️ Pytest错误输出：\n{result.stderr}")
                if result.returncode == 0:
                    self.log_signal.emit("✅ 促销用例执行成功！")
                else:
                    self.log_signal.emit(f"❌ 促销用例执行失败（返回码：{result.returncode}）")

            elif self.case_type == "report":
                self.log_signal.emit("========== 开始执行Allure HTML报告生成脚本 ==========")
                # 检查报告脚本是否存在
                if not os.path.exists(self.paths["report"]):
                    self.log_signal.emit(f"❌ 找不到文件：{self.paths['report']}")
                    return

                # 执行allure_html.py
                cmd = [self.python_exe, self.paths["report"]]
                self.log_signal.emit(f"📌 执行命令：{' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    timeout=300
                )

                if result.stdout:
                    self.log_signal.emit(f"📝 脚本输出：\n{result.stdout}")
                if result.stderr:
                    self.log_signal.emit(f"⚠️ 脚本错误输出：\n{result.stderr}")
                if result.returncode == 0:
                    self.log_signal.emit("✅ Allure HTML报告脚本执行成功！")
                else:
                    self.log_signal.emit(f"❌ Allure HTML报告脚本执行失败（返回码：{result.returncode}）")

        except subprocess.TimeoutExpired:
            self.log_signal.emit(f"❌ {'登录用例' if self.case_type=='login' else '促销用例' if self.case_type=='promo' else '报告脚本'}执行超时（5分钟），强制终止！")
        except Exception as e:
            error_detail = traceback.format_exc()
            self.log_signal.emit(f"❌ 执行异常：{str(e)}")
            self.log_signal.emit(f"📝 详细错误：\n{error_detail}")
        finally:
            case_name = {
                "login": "登录",
                "promo": "促销",
                "report": "Allure HTML报告生成"
            }.get(self.case_type, "未知")
            self.log_signal.emit(f"========== {case_name}用例/脚本执行结束 ==========\n")
            self.finish_signal.emit()

# ========== 主界面类（无修改） ==========
class CaseRunnerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("悟之信息自动化测试平台")
        self.setFixedSize(950, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.login_btn = QPushButton("运行登录用例")
        self.login_btn.setFont(QFont("微软雅黑", 12))
        self.login_btn.setFixedSize(180, 50)
        self.login_btn.clicked.connect(self.start_login_case)
        btn_layout.addWidget(self.login_btn)

        self.promo_btn = QPushButton("运行促销用例")
        self.promo_btn.setFont(QFont("微软雅黑", 12))
        self.promo_btn.setFixedSize(180, 50)
        self.promo_btn.clicked.connect(self.start_promo_case)
        btn_layout.addWidget(self.promo_btn)

        self.report_btn = QPushButton("促销用例生成AllureHTML报告")
        self.report_btn.setFont(QFont("微软雅黑", 12))
        self.report_btn.setFixedSize(270, 50)
        self.report_btn.clicked.connect(self.start_report_script)
        btn_layout.addWidget(self.report_btn)

        main_layout.addLayout(btn_layout)

        # 结果显示区域
        result_label = QLabel("用例/脚本运行结果")
        result_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        main_layout.addWidget(result_label)

        self.result_text = QTextEdit()
        self.result_text.setFont(QFont("微软雅黑", 11))
        self.result_text.setReadOnly(True)
        main_layout.addWidget(self.result_text)

    def write_log(self, content):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.result_text.append(f"[{timestamp}] {content}")

    def start_login_case(self):
        self.login_btn.setEnabled(False)
        self.login_thread = CaseThread(case_type="login")
        self.login_thread.log_signal.connect(self.write_log)
        self.login_thread.finish_signal.connect(lambda: self.login_btn.setEnabled(True))
        self.login_thread.start()

    def start_promo_case(self):
        self.promo_btn.setEnabled(False)
        self.promo_thread = CaseThread(case_type="promo")
        self.promo_thread.log_signal.connect(self.write_log)
        self.promo_thread.finish_signal.connect(lambda: self.promo_btn.setEnabled(True))
        self.promo_thread.start()

    def start_report_script(self):
        self.report_btn.setEnabled(False)
        self.report_thread = CaseThread(case_type="report")
        self.report_thread.log_signal.connect(self.write_log)
        self.report_thread.finish_signal.connect(lambda: self.report_btn.setEnabled(True))
        self.report_thread.start()

# ========== 程序入口 ==========
if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    window = CaseRunnerWindow()
    window.show()
    sys.exit(app.exec())