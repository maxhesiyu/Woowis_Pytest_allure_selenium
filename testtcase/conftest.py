import pytest
from selenium import webdriver

from common.log import log as logger
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


# ===================== 通用核心函数（抽离复用） =====================
def get_pcno_pwd_list():
    """【全局通用】单独读取账号密码.xlsx，返回[{pcno:xxx, password:xxx}, ...]"""
    pwd_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path("账号密码.xlsx")),
        sheet_name="Sheet2",
        parse_sku=False,
        sku_col_index=0
    )
    # 增强：过滤空行，避免无效数据
    valid_pwd_data = [{"pcno": row[0], "password": row[1]} for row in pwd_data if row and len(row) >= 2]
    logger.info(f"账号密码有效行数：{len(valid_pwd_data)}")
    return valid_pwd_data


def get_merged_business_with_pwd_data(
        business_excel_name,
        business_sheet_name,
        parse_sku,
        sku_col_index,
        business_data_mapper
):
    """
    【通用合并函数】合并任意业务表格 + 账号密码表格（自动取最少行数）
    :param business_excel_name: 业务表格文件名（如"促销赠品获取参数化.xlsx"）
    :param business_sheet_name: 业务表格sheet名（如"促销"）
    :param parse_sku: 是否解析SKU（传给read_test_data_from_excel）
    :param sku_col_index: SKU列索引（传给read_test_data_from_excel）
    :param business_data_mapper: 业务数据映射函数，入参(业务行, 账号密码行, 行索引)，返回合并后的字典
    :return: 合并后的数据列表
    """
    # 1. 读取业务数据
    business_data = read_test_data_from_excel(
        file_path=str(get_excel_file_path(business_excel_name)),
        sheet_name=business_sheet_name,
        parse_sku=parse_sku,
        sku_col_index=sku_col_index
    )
    # 过滤业务数据空行
    valid_business_data = [row for row in business_data if row and len(row) > 0]

    # 2. 读取账号密码数据（复用全局通用函数）
    valid_pwd_data = get_pcno_pwd_list()

    # 3. 打印原始数据行数（关键排查）
    logger.info(f"【{business_excel_name}】业务有效行数：{len(valid_business_data)}")
    logger.info(f"【{business_excel_name}】账号密码有效行数：{len(valid_pwd_data)}")

    # 4. 取最小行数，截断数据（核心优化：不再抛错，只执行最少行数）
    min_row_count = min(len(valid_business_data), len(valid_pwd_data))
    if min_row_count < len(valid_business_data):
        logger.warning(
            f"【{business_excel_name}】行数不足！业务数据{len(valid_business_data)}行 > 账号密码{len(valid_pwd_data)}行，仅执行前{min_row_count}行")
    truncated_business = valid_business_data[:min_row_count]
    truncated_pwd = valid_pwd_data[:min_row_count]

    # 5. 合并数据（【修改点1】：新增index参数，传给映射函数生成唯一标识）
    merged_data = []
    for index, (business_case, pwd_info) in enumerate(zip(truncated_business, truncated_pwd)):
        # 映射函数新增index参数，用于生成唯一ID
        merged_case = business_data_mapper(business_case, pwd_info, index)
        merged_data.append(merged_case)

    logger.info(f"【{business_excel_name}】最终合并有效行数：{len(merged_data)}")
    return merged_data


# ===================== 业务专属映射函数（仅需定义字段映射） =====================
def free_gift_data_mapper(business_case, pwd_info, index):
    """
    促销赠品业务：字段映射规则
    【修改点2】：新增index参数，生成唯一case_id（源头区分用例）
    """
    # 生成唯一case_id：业务类型+索引+用例名+账号（确保绝对唯一）
    unique_case_id = f"free_gift_{index}_{business_case[0]}_{pwd_info['pcno']}"
    return {
        "case_id": unique_case_id,  # 新增：唯一用例ID（核心修复点）
        "case_name": business_case[0],
        "skuTime": business_case[1],
        "sku_list": business_case[2],
        "expected_result": business_case[3],
        "pcno": pwd_info["pcno"],
        "password": pwd_info["password"],
        "index": index  # 备用：行索引
    }


def login_data_mapper(business_case, pwd_info, index):
    """
    登录业务：字段映射规则
    【修改点3】：新增index参数，生成唯一case_id
    """
    unique_case_id = f"login_{index}_{business_case[0]}_{pwd_info['pcno']}"
    return {
        "case_id": unique_case_id,  # 新增：唯一用例ID
        "case_name": business_case[0],  # 登录用例名
        "expected_result": business_case[1],  # 登录预期结果
        "pcno": pwd_info["pcno"],  # 匹配的账号
        "password": pwd_info["password"],  # 匹配的密码
        "index": index  # 备用：行索引
    }


# ===================== 业务专属合并函数（极简调用通用函数） =====================
def get_merged_free_gift_data():
    """【促销用例】合并促销数据+账号密码（调用通用函数）"""
    return get_merged_business_with_pwd_data(
        business_excel_name="促销赠品获取参数化.xlsx",
        business_sheet_name="促销",
        parse_sku=True,
        sku_col_index=2,
        business_data_mapper=free_gift_data_mapper  # 传入促销专属映射规则
    )


def get_merged_login_data():
    """【登录用例】合并登录数据+账号密码（调用通用函数）"""
    return get_merged_business_with_pwd_data(
        business_excel_name="测试登录参数化.xlsx",
        business_sheet_name="Sheet1",
        parse_sku=False,
        sku_col_index=2,
        business_data_mapper=login_data_mapper  # 传入登录专属映射规则
    )


# ===================== Fixture定义 =====================
@pytest.fixture(params=get_pcno_pwd_list())
def pcno_pwd_fixture(request):
    """参数化Fixture：单独使用多套账号密码（备用）"""
    return request.param


# 【修改点4】：先获取数据，再为Fixture指定唯一ids（核心修复Allure合并问题）
free_gift_data = get_merged_free_gift_data()  # 提前获取合并后的促销数据
@pytest.fixture(
    params=free_gift_data,
    ids=[case["case_id"] for case in free_gift_data]  # 基于唯一case_id生成ids
)
def merged_free_gift_fixture(request):
    """促销用例Fixture：1套促销数据 ↔ 1套账号密码"""
    return request.param


# 【修改点5】：登录Fixture同理，添加唯一ids
login_data = get_merged_login_data()  # 提前获取合并后的登录数据
@pytest.fixture(
    params=login_data,
    ids=[case["case_id"] for case in login_data]  # 基于唯一case_id生成ids
)
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
                    except Exception as e:
                        logger.error(f"❌ 失败截图失败：{e}")
                break