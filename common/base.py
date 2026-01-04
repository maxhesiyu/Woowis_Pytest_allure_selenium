import allure
import time

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
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


@allure.step('鼠标悬停')
def sel_hover(driver, locator, timeout=10):
    order_elem = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )
    # 执行悬停动作
    actions = ActionChains(driver)
    actions.move_to_element(order_elem)  # 仅悬停，不点击
    actions.perform()  # 必须调用perform()生效

@allure.step('获取元素文本')
def get_text(driver, locator, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        return elem.text.strip()
    except Exception as e:
        log.error(f"获取文本失败：{locator} → {e}")
        return ""

@allure.step('等待指定元素出现后刷新页面')
def refresh_when_element_appears(driver, target_locator,core_element_loc, wait_timeout=15, refresh_type="normal"):
    """
    检测到目标元素出现后刷新页面
    :param driver: 浏览器驱动对象
    :param target_locator: 目标元素定位符（元组），如 (By.XPATH, "//div[@class='error']")
    :param core_element_loc: 刷新后等待核心元素加载【关键】页面的核心元素，确保刷新后页面可用
    :param wait_timeout: 等待元素出现的超时时间（秒）
    :param refresh_type: 刷新类型（normal=普通刷新，force=强制刷新）
    :return: 布尔值（True=元素出现并刷新，False=元素未出现）
    """
    try:
        # 1. 显式等待目标元素出现（可选：presence/visibility，按需选择）
        # presence：元素存在于DOM（不可见也会触发）；visibility：元素可见才触发
        wait = WebDriverWait(driver, wait_timeout)
        wait.until(EC.presence_of_element_located(target_locator))  # 推荐用presence（更广的触发条件）
        # wait.until(EC.visibility_of_element_located(target_locator))  # 仅元素可见时触发
        print(f"检测到元素 {target_locator} 出现，执行页面刷新")
        # 2. 执行刷新（可选普通/强制刷新）
        if refresh_type == "force":
            # 强制刷新（忽略缓存，推荐页面异常时用）
            driver.execute_script("location.reload(true);")
        else:
            # 普通刷新（等效F5，默认）
            driver.refresh()
        # 3. 刷新后等待核心元素加载（避免后续操作失效）
        # 【关键】替换为你页面的核心元素，确保刷新后页面可用
        WebDriverWait(driver, wait_timeout).until(EC.element_to_be_clickable(core_element_loc))
        return True

    except TimeoutException as e:
        # 超时未检测到元素，不刷新
        print(f"超时 {wait_timeout} 秒未检测到元素 {target_locator}，不刷新")
        log.info(e)
        return False


@allure.step('重定向页面')
def redirect_URL(driver, URL_KEY, timeout=10):
    original_handle = driver.current_window_handle   #原始窗口的驱动
    TARGET_URL_KEY = URL_KEY  # 重定向后的URL关键词
    # 1. 点击元素触发重定向/新标签页
    sel_click(driver, (By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]"))
    # 2. 分情况处理重定向
    allure.story("重定向页面")
    if len(driver.window_handles) > 1:
        # 情况1：重定向到新标签页（你的场景）
        WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
        # 切换到新标签页
        new_handle = [h for h in driver.window_handles if h != original_handle][0]
        driver.switch_to.window(new_handle)
        # 等待新标签页URL完成重定向
        WebDriverWait(driver, timeout).until(EC.url_contains(TARGET_URL_KEY))
    else:
        # 情况2：同标签页重定向
        WebDriverWait(driver, 10).until(EC.url_contains(TARGET_URL_KEY))


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