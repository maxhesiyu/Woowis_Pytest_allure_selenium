from time import sleep

from openpyxl.reader.excel import load_workbook
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from common.base import get_all_visible_text
from common.log import log
from config.config import ENV, env
from po.event import ZhuCe
from read_excel.read_from_excel import read_test_data_from_excel
from pathlib import Path
import pytest
import allure
from selenium.webdriver.common.keys import Keys


# ========== 前置操作函数（保留，配置化） ==========
def execute_pre_operation(driver, operation_name):
    operation_map = {
        "清空密码": lambda: (
            driver.find_element(By.XPATH, "//input[@placeholder='密码(Password)']").send_keys(Keys.CONTROL, 'a'),
            driver.find_element(By.XPATH, "//input[@placeholder='密码(Password)']").send_keys(Keys.DELETE)
        ),
        "无": lambda: None
    }
    if operation_name in operation_map:
        operation_map[operation_name]()
        log.info(f"执行前置操作：{operation_name}")
    else:
        log.warning(f"未识别的前置操作：{operation_name}")


# ========== 测试类（无定位符，全局文本断言） ==========
class TestLogin:
    # 项目路径配置
    PROJECT_ROOT = Path(__file__).parent.parent.absolute()
    EXCEL_FILE_PATH = PROJECT_ROOT / "测试登录参数化.xlsx"

    @pytest.mark.parametrize(
        "test_case",
        read_test_data_from_excel(
            file_path=str(EXCEL_FILE_PATH),
            sheet_name="Sheet1",
            parse_sku=False,  # 无SKU，显式传False
            sku_col_index=0  # 无SKU，显式传任意索引
        )
    )
    @allure.story('登录测试（全局文本断言')
    def test_login(self, test_case, open_page):
        # 解析Excel数据（无定位符列）
        case_name = test_case[0]
        pcno = test_case[1]
        password = test_case[2]
        expected_result = test_case[3]
        pre_operation = test_case[4]
        driver = open_page

        allure.dynamic.title(f"登录测试：{case_name}")
        log.info(f"📌 执行用例：{case_name}，预期结果：{expected_result}")

        try:
            # 步骤1：输入账号密码
            with allure.step(f"输入顾客编号: {pcno}"):
                pc_input = driver.find_element(By.XPATH, "//input[@placeholder='顾客编号(PC ID)']")
                pc_input.clear()
                pc_input.send_keys(pcno)

            with allure.step(f"输入密码: {password if password else '空'}"):
                pwd_input = driver.find_element(By.XPATH, "//input[@placeholder='密码(Password)']")
                pwd_input.clear()
                if password:
                    pwd_input.send_keys(password)

            # 步骤2：执行前置操作
            if pre_operation != "无":
                with allure.step(f"执行前置操作：{pre_operation}"):
                    execute_pre_operation(driver, pre_operation)

            # 步骤3：点击登录 + 等待页面跳转（核心优化）
            with allure.step("点击登录按钮并等待页面跳转"):
                # 记录登录前的URL
                original_url = driver.current_url
                driver.find_element(By.XPATH, "//span[contains(text(),'登录(Login)')]").click()

            # 判断页面URL是否发生变化，发生变化留出3秒的等待页面渲染时间
            with allure.step("判断URL是否发生变化"):
                sleep(1)
                current_url = driver.current_url
                if current_url != original_url:
                    # URL变更 → 延迟3秒，给新页面渲染文本
                    log.info(f"✅ URL已变更：{original_url} → {current_url}，延迟3秒等待渲染")
                    sleep(3)
                else:
                    # URL未变更 → 立即执行判断，不延迟
                    log.warning(f"⚠️ URL未变更，仍停留在：{original_url}，立即执行判断")


            # ========== 核心：全局文本扫描 + 断言 ==========
            with allure.step("抓取页面所有可见文本（含弹窗）并断言预期结果"):
                # 抓取全页面文本（包括弹窗）
                all_page_text = get_all_visible_text(driver)
                # 模糊断言查找
                assert any(expected_result in text for text in all_page_text), \
                    f"断言失败！未找到包含「{expected_result}」的文本。页面文本：{all_page_text}"


        except Exception as e:
            # 失败时附加截图+全局文本，便于排查
            with allure.step("用例执行失败，附加截图和页面文本"):
                allure.attach(
                    driver.get_screenshot_as_png(),
                    f"失败截图：{case_name}",
                    allure.attachment_type.PNG
                )
                # 附加页面所有文本，方便排查
                all_page_text = get_all_visible_text(driver)
                allure.attach(
                    f"页面所有文本：{all_page_text}",
                    f"页面文本：{case_name}",
                    allure.attachment_type.TEXT
                )
            log.error(f"❌ 用例「{case_name}」执行失败：{str(e)}")
            raise


    @allure.title('用户注册流程')
    def test_ZhuCe_01(self,open_page):
        with allure.step("用户注册流程"):
            driver = open_page
            allure.dynamic.title("用户注册流程")
            ZhuCe(driver,env.randomPhone,ENV.CAPTCHA,ENV.referrer,ENV.name,ENV.npwd,ENV.ncpwd,env.randomSFZ)









