from venv import logger

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

# 封装：单独获取账号密码（返回列表，元素为字典）
# ===================== 核心函数=====================
def get_pcno_pwd_list():
    """【全局通用】单独读取账号密码.xlsx，返回[{pcno:xxx, password:xxx}, ...]"""
    pwd_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path("账号密码.xlsx")),
        sheet_name="Sheet2",
        parse_sku=False,
        sku_col_index=0
    )
    # 增强：过滤空行，避免无效数据
    return [{"pcno": row[0], "password": row[1]} for row in pwd_data if row and len(row) >= 2]

@pytest.fixture(params=get_pcno_pwd_list())
def pcno_pwd_fixture(request):
    """参数化Fixture：单独使用多套账号密码（备用）"""
    return request.param

def get_merged_free_gift_data():
    """【促销用例】合并促销数据+账号密码（1:1匹配）"""
    gift_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path("促销赠品获取参数化.xlsx")),
        sheet_name='促销',
        parse_sku=True,
        sku_col_index=2
    )
    pwd_list = get_pcno_pwd_list()
    # 新增：打印原始数据行数（关键排查）
    logger.info(f"促销数据原始行数：{len(gift_data)}")
    logger.info(f"账号密码数据行数：{len(pwd_list)}")

    if len(gift_data) > len(pwd_list):
        raise ValueError(
            f"账号密码行数不足！促销数据{len(gift_data)}行 > 账号密码{len(pwd_list)}行")

    merged_data = []
    for gift_case, pwd_info in zip(gift_data, pwd_list):
        merged_data.append({
            "case_name": gift_case[0],
            "skuTime": gift_case[1],
            "sku_list": gift_case[2],
            "expected_result": gift_case[3],
            "pcno": pwd_info["pcno"],
            "password": pwd_info["password"]
        })
    return merged_data

@pytest.fixture(params=get_merged_free_gift_data())
def merged_free_gift_fixture(request):
    """促销用例Fixture：1套促销数据 ↔ 1套账号密码"""
    return request.param

# ===================== 登录用例合并逻辑（和促销逻辑统一）=====================
def get_merged_login_data():
    """【登录用例】合并登录数据+账号密码（1:1匹配，复用通用密码逻辑）"""
    # 1. 读取登录业务数据
    login_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path("测试登录参数化.xlsx")),
        sheet_name='Sheet1',
        parse_sku=False,
        sku_col_index=2
    )
    # 2. 复用全局账号密码逻辑（无需重复写）
    pwd_list = get_pcno_pwd_list()
    # 新增：打印原始数据行数
    logger.info(f"登录数据原始行数：{len(login_data)}")
    logger.info(f"账号密码数据行数：{len(pwd_list)}")

    # 3. 行数校验（和促销用例一致）
    # if len(login_data) > len(pwd_list):
    #     raise ValueError(
    #         f"账号密码行数不足！登录数据{len(login_data)}行 > 账号密码{len(pwd_list)}行")

    # 4. 1:1合并（结构和促销保持一致，便于维护）
    merged_data = []
    for login_case, pwd_info in zip(login_data, pwd_list):
        merged_data.append({
            "case_name": login_case[0],       # 登录用例名
            "expected_result": login_case[1], # 登录预期结果
            "pcno": pwd_info["pcno"],         # 匹配的账号
            "password": pwd_info["password"]  # 匹配的密码
        })
    return merged_data

# 登录用例专属Fixture（和促销Fixture逻辑完全统一）
@pytest.fixture(params=get_merged_login_data())
def merged_login_fixture(request):
    """登录用例Fixture：1套登录数据 ↔ 1套账号密码"""
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