import allure
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from common.log import log
from config.config import ALLURE_IMG_DIR


# ========== 核心操作封装 ==========
@allure.step('鼠标左键点击')
def sel_click(driver, locator, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()
        time.sleep(0.2)
    except Exception as e:
        log.error(f"点击元素失败：{locator} → {e}")
        raise

@allure.step('输入框输入数值')
def sel_end_keys(driver, locator, value, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        elem.clear()
        elem.send_keys(str(value))  # 强制转字符串，避免数字输入异常
        time.sleep(0.2)
    except Exception as e:
        log.error(f"输入失败：{locator} → {e}")
        raise

@allure.step('获取元素文本')
def get_text(driver, locator, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        return elem.text.strip()
    except Exception as e:
        log.error(f"获取文本失败：{locator} → {e}")
        return ""


# ========== 断言封装（修复文本获取错误） ==========
@allure.step('断言文字存在于元素中')
def assert_text_in_element(driver, locator, target_text, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
        elem_text = elem.text.strip()  # 修复：正确获取文本
        assert target_text in elem_text, \
            f"预期包含：{target_text} | 实际：{elem_text} | 定位符：{locator}"
    except TimeoutException as e:
        error_msg = f"元素定位超时（{timeout}秒）：{locator}"
        log.error(error_msg)
        raise AssertionError(error_msg) from e
    except AssertionError as e:
        log.error(f"断言失败：{e}")
        raise
    except Exception as e:
        log.error(f"断言异常：{e}")
        raise AssertionError(f"断言异常：{e}") from e

# ========== 截图封装（整合原screenshot.py） ==========
@allure.step('失败截图并附加到报告')
def attach_failure_screenshot(driver, name="失败截图"):
    try:
        timestamp = time.strftime("%Y%m%d%H%M%S")
        filepath = ALLURE_IMG_DIR / f"{name}_{timestamp}.png"
        driver.save_screenshot(str(filepath))
        with open(filepath, "rb") as f:
            allure.attach(f.read(), name=name, attachment_type=allure.attachment_type.PNG)
        log.info(f"截图保存：{filepath}")
    except Exception as e:
        log.error(f"截图失败：{e}")