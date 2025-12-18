import pytest
from selenium import webdriver

from common.base import attach_failure_screenshot
from config.config import ENV
from po import event


# ========== 核心Fixture：open_page（未登录的浏览器） ==========
@pytest.fixture(scope='function')
def open_page():
    """未登录的浏览器实例（修复：使用局部变量管理driver）"""
    driver = None  # 局部变量，避免全局污染
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", False)  # 用例结束后自动关闭
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        driver.get(ENV.URL)
        driver.maximize_window()
        yield driver  # 返回当前driver实例
    except Exception as e:
        print(f"❌ open_page fixture 失败：{e}")
        raise
    finally:
        # 确保销毁当前driver实例（仅在driver初始化成功时执行）
        if driver:
            try:
                driver.quit()
                print(f"✅ 驱动进程已销毁：{driver.session_id}")
            except Exception as e:
                print(f"⚠️ 销毁driver失败：{e}")


# ========== 核心Fixture：DengLu（已登录的浏览器） ==========
@pytest.fixture(scope='function')
def DengLu():
    """已登录的浏览器实例（修复：使用局部变量管理driver）"""
    driver = None  # 局部变量，避免全局污染
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", False)  # 改为False，避免浏览器残留
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        driver.maximize_window()
        driver.implicitly_wait(10)
        event.myo_login(driver, ENV.URL, ENV.pcno, ENV.password)
        yield driver  # 返回当前driver实例
    except Exception as e:
        print(f"❌ DengLu fixture 失败：{e}")
        raise
    finally:
        # 确保销毁当前driver实例
        if driver:
            try:
                driver.quit()
                print(f"✅ 驱动进程已销毁：{driver.session_id}")
            except Exception as e:
                print(f"⚠️ 销毁driver失败：{e}")


# ========== 全局失败截图钩子 ==========
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        for fixture_name in ("open_page", "DengLu"):
            if fixture_name in item.fixturenames:
                driver = item.funcargs.get(fixture_name)  # 从fixture参数中获取当前driver
                if driver:
                    try:
                        attach_failure_screenshot(driver, name=f"用例失败_{item.name}")
                    except:
                        pass
                break