import pytest
from selenium import webdriver

from common.log import log as logger
from common.base import attach_failure_screenshot
from config.config import ENV
from po import event

# ========== 全局开关【核心】✅ 想关闭浏览器就改为 False，想保活就改为 True ==========
KEEP_BROWSER_OPEN = False

# ========== 核心Fixture：open_page（未登录的浏览器） ==========
@pytest.fixture(scope='function')
def open_page():
    driver = None
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", KEEP_BROWSER_OPEN)  # 绑定开关
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        driver.get(ENV.URL)
        driver.maximize_window()
        driver.implicitly_wait(10)
        yield driver
    except Exception as e:
        logger.error(f"❌ open_page fixture 失败：{e}")
        raise
    finally:
        # 只有开关为False时，才执行销毁逻辑，True则不执行
        if driver and not KEEP_BROWSER_OPEN:
            try:
                driver.quit()  # 推荐用quit，比close彻底
                logger.info(f"✅ 驱动进程已销毁：{driver.session_id}")
            except Exception as e:
                logger.warning(f"⚠️ 销毁driver失败：{e}")


# ========== 核心Fixture：DengLu（已登录的浏览器） ==========
@pytest.fixture(scope='function')
def DengLu():
    driver = None
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", KEEP_BROWSER_OPEN)  # 绑定开关
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        driver.maximize_window()
        driver.implicitly_wait(10)
        event.myo_login(driver, ENV.URL, ENV.pcno, ENV.password)
        yield driver
    except Exception as e:
        logger.error(f"❌ DengLu fixture 失败：{e}")
        raise
    finally:
        # 只有开关为False时，才执行销毁逻辑，True则不执行
        if driver and not KEEP_BROWSER_OPEN:
            try:
                driver.quit()
                logger.info(f"✅ 驱动进程已销毁：{driver.session_id}")
            except Exception as e:
                logger.warning(f"⚠️ 销毁driver失败：{e}")


# ========== 全局失败截图钩子 ==========
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
                    except Exception as e:
                        logger.error(f"❌ 失败截图失败：{e}")
                break