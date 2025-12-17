import pytest
from selenium import webdriver

from common.base import attach_failure_screenshot
from config.config import ENV
from po import event


# ========== 核心Fixture：open_page（未登录的浏览器） ==========
@pytest.fixture(scope='class')  # 与用例的function级别匹配
def open_page():
    """未登录的浏览器实例（修复：确保fixture能正常返回driver）"""
    global driver
    try:
        option = webdriver.EdgeOptions()
        # true浏览器窗口不会自动关闭，保持打开状态,False Selenium自动终止浏览器进程，窗口立即关闭；
        option.add_experimental_option("detach", False)
        option.add_experimental_option("excludeSwitches", ["enable-automation"])  # 避免浏览器提示自动化
        driver = webdriver.Edge(options=option)
        driver.get(ENV.URL)
        driver.maximize_window()
        yield driver  # 返回driver给用例
    except Exception as e:
        print(f"❌ open_page fixture 失败：{e}")
        raise
    # finally:
    #     driver.quit()


# ========== 核心Fixture：DengLu（已登录的浏览器） ==========
@pytest.fixture(scope='function')
def DengLu():
    """已登录的浏览器实例"""
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", True)
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        # 窗口最大化
        driver.maximize_window()
        driver.implicitly_wait(10)  # 隐式等待，10秒内页面元素加载完成后立即执行
        # 执行登录操作
        event.myo_login(driver,ENV.URL, ENV.pcno, ENV.password)
        yield driver
    except Exception as e:
        print(f"❌ DengLu fixture 失败：{e}")
        raise
    # finally:
    #     driver.quit()


# ========== 全局失败截图钩子（可选，注释不影响fixture加载） ==========
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        for fixture_name in ("open_page", "DengLu"):
            if fixture_name in item.fixturenames:
                driver = item.funcargs.get(fixture_name)
                if driver:
                    try:
                        attach_failure_screenshot(driver, name=f"用例失败_{item.name}")
                    except:
                        pass  # 截图失败不影响用例结果
                break