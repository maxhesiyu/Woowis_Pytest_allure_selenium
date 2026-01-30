import pytest
from selenium import webdriver

from common.base import attach_failure_screenshot
from config.config import ENV
from config.path_config import get_excel_file_path
from config.read_from_excel import read_test_data_from_excel
from po import event

# ========== 全局开关【核心】✅ 想关闭浏览器就改为 False，想保活就改为 True ==========
KEEP_BROWSER_OPEN = False

# ========== 核心Fixture：open_page（未登录的浏览器） ==========
@pytest.fixture(scope='function')
def open_page():
    driver = None
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", KEEP_BROWSER_OPEN) # 绑定开关
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        driver.get(ENV.URL)
        driver.maximize_window()
        driver.implicitly_wait(10)
        yield driver
    except Exception as e:
        print(f"❌ open_page fixture 失败：{e}")
        raise
    finally:
        # 只有开关为False时，才执行销毁逻辑，True则不执行
        if driver and not KEEP_BROWSER_OPEN:
            try:
                driver.quit() # 推荐用quit，比close彻底
                print(f"✅ 驱动进程已销毁：{driver.session_id}")
            except Exception as e:
                print(f"⚠️ 销毁driver失败：{e}")

# ========== 核心Fixture：DengLu（已登录的浏览器） ==========
@pytest.fixture(scope='function')
def DengLu():
    driver = None
    try:
        option = webdriver.EdgeOptions()
        option.add_experimental_option("detach", KEEP_BROWSER_OPEN) # 绑定开关
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Edge(options=option)
        driver.maximize_window()
        driver.implicitly_wait(10)
        event.myo_login(driver, ENV.URL, ENV.pcno, ENV.password)
        yield driver
    except Exception as e:
        print(f"❌ DengLu fixture 失败：{e}")
        raise
    finally:
        # 只有开关为False时，才执行销毁逻辑，True则不执行
        if driver and not KEEP_BROWSER_OPEN:
            try:
                driver.quit()
                print(f"✅ 驱动进程已销毁：{driver.session_id}")
            except Exception as e:
                print(f"⚠️ 销毁driver失败：{e}")

# ===================合并两个Excel表格文件======================
def get_merged_login_data():
    """
    合并两个Excel的数据：
    - 账号密码.xlsx：pcno（第0列）、password（第1列）
    - 测试登录参数化.xlsx：case_name（第0列）、expected_result（第1列）
    注：需保证两个Excel的行数一致，否则会截断到较短的行数
    """
    # 1. 读取账号密码数据（Excel文件夹下的 账号密码.xlsx）
    pwd_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path("账号密码.xlsx")),
        sheet_name="Sheet1",
        parse_sku=False,
        sku_col_index=0
    )
    # 2. 读取用例名+预期结果数据（Excel文件夹下的 测试登录参数化.xlsx）
    case_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path("测试登录参数化.xlsx")),
        sheet_name="Sheet1",
        parse_sku=False,
        sku_col_index=0
    )
    # 3. 一一对应合并数据（zip 保证行数一致，多余行被截断）
    merged_data = []
    for pwd_row, case_row in zip(pwd_data, case_data):
        merged_data.append({
            "case_name": case_row[0],        # 来自测试登录参数化.xlsx 第0列
            "expected_result": case_row[1],  # 来自测试登录参数化.xlsx 第1列
            "pcno": pwd_row[0],              # 来自账号密码.xlsx 第0列
            "password": pwd_row[1]           # 来自账号密码.xlsx 第1列
        })
    return merged_data

# 定义全局Fixture（pytest 自动识别，所有测试文件可直接使用）
@pytest.fixture(params=get_merged_login_data())
def merged_login_fixture(request):
    """合并后的试数据Fixture：包含case_name/expected_result/pcno/password"""
    return request.param


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
                    except:
                        pass
                break