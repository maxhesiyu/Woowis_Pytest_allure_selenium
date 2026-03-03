from time import sleep
import pytest
import allure
from selenium.webdriver.common.by import By

from common.base import sel_click, refresh_when_element_appears, redirect_URL, \
    sel_hover, check_text_exists
from common.log import log
from common.selenium_login import login_and_verify
from config.excel_config import EXCEL_PATHS, EXCEL_READ_CONFIG, EXCEL_MERGE_CONFIG  # 导入配置
from common.read_excel_pandas import ExcelHandler
from po.shopping import Shopping_querySku


# ====================== 测试数据加载（基于配置文件） ======================
def load_free_gift_test_data():
    """加载赠品测试数据（封装为函数，便于复用/调试）"""
    # 构建Excel合并配置列表
    excel_config_list = [
        {
            "file_path": EXCEL_PATHS["account"],
            **EXCEL_READ_CONFIG["free_gift"]["account"]
        },
        {
            "file_path": EXCEL_PATHS["promotion"],
            **EXCEL_READ_CONFIG["free_gift"]["promotion"]
        }
    ]
    # 读取合并配置
    merge_config = EXCEL_MERGE_CONFIG["free_gift"]

    try:
        merged_df = ExcelHandler.merge_excel(
            excel_config_list=excel_config_list,
            key_column=merge_config["key_column"],
            merge_how=merge_config["merge_how"],
            preserve_all_fields=merge_config["preserve_all_fields"]
        )
        # 可选：打印数据详情（调试用）
        # ExcelHandler.print_data_detail(merged_df)
        test_data_list = merged_df.to_dict('records')
        log.info(f"✅ 赠品测试数据加载成功，共{len(test_data_list)}条")
        return test_data_list
    except Exception as e:
        log.error(f"❌ 赠品测试数据加载失败：{str(e)}")
        raise


# 加载测试数据
MERGED_TEST_DATA = load_free_gift_test_data()


# ====================== 测试用例逻辑 ======================
@allure.title('用户获取不同赠品')
class TestFreeGift:

    @pytest.mark.parametrize("test_data", MERGED_TEST_DATA)
    @allure.title('用户获取不同促销：{test_data[场景]}')
    def test_shopping_FreeGift(self, open_page, test_data):
        """用户获取不同促销赠品测试"""
        # 1. 读取测试数据（解构赋值）
        case_id = test_data["序号"]
        case_name = test_data["场景"]
        sku_list = test_data["SKU"]
        sku_time = test_data["SKUTime"]
        password = test_data["密码"]
        pcno = test_data["账号"]
        expected_result = test_data["预期结果"]
        driver = open_page

        # 2. 空值提示（优化日志和allure附件）
        empty_hints = []
        if not pcno:
            empty_hints.append("账号为空")
            log.warning(f"用例[{case_id}-{case_name}]账号为空，将使用空值执行登录")
        if not password:
            empty_hints.append("密码为空")
            log.warning(f"用例[{case_id}-{case_name}]密码为空，将使用空值执行登录")

        # 动态更新用例标题
        empty_mark = f"【{','.join(empty_hints)}】" if empty_hints else ""
        allure.dynamic.title(f"{case_name}（序号：{case_id}）{empty_mark}")
        if empty_hints:
            allure.attach(f"⚠️ {','.join(empty_hints)}，将使用空值执行登录", "数据提示", allure.attachment_type.TEXT)

        # 3. 登录操作
        with allure.step(f"登录账号：{pcno}"):
            try:
                login_and_verify(driver, pcno, password)
            except Exception as e:
                error_msg = f"登录失败：{str(e)}"
                allure.attach(error_msg, "登录结果", allure.attachment_type.TEXT)
                pytest.fail(f"用例[{case_id}-{case_name}] {error_msg}")

        # 4. 加购并验证促销
        with allure.step("加入购物车并验证促销赠品"):
            # 页面跳转与刷新（封装后更简洁）
            refresh_when_element_appears(
                driver,
                (By.XPATH, "//span[contains(text(),'确定')]"),
                (By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]")
            )
            redirect_URL(driver, "order/product", (By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]"))

            # 进入产品列表
            sel_click(driver, (By.XPATH, "//a[@class='top-link']//span[@class='zh'][contains(text(),'产品')]"))
            sleep(1)

            # 循环加购（类型转换优化）
            with allure.step(f"循环{sku_time}次加购SKU：{sku_list}"):
                try:
                    sku_time_int = int(sku_time)
                except (ValueError, TypeError) as e:
                    error_msg = f"SKUTime格式错误：{sku_time}（需为整数），错误：{str(e)}"
                    allure.attach(error_msg, "数据错误", allure.attachment_type.TEXT)
                    pytest.fail(f"用例[{case_id}-{case_name}] {error_msg}")

                for _ in range(sku_time_int):
                    Shopping_querySku(driver, sku_list)

            # 购物车操作
            sel_hover(driver, (By.XPATH, "//a[@class='item']//span[@class='zh'][contains(text(),'购物车')]"))
            sleep(1)
            sel_click(driver, (By.XPATH, "//span[contains(text(),'去结算(Go to pay)')]"))

            # 验证预期结果
            with allure.step(f"验证预期结果：{expected_result}"):
                if check_text_exists(driver, expected_result):
                    success_msg = f"✅ 用例[{case_id}-{case_name}]验证通过：预期文本存在"
                    allure.attach(success_msg, "验证结果")
                    log.info(success_msg)
                else:
                    fail_msg = f"❌ 用例[{case_id}-{case_name}]验证失败：预期文本「{expected_result}」不存在"
                    allure.attach(fail_msg, "验证结果")
                    pytest.fail(fail_msg)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--alluredir", "./allure-results"])