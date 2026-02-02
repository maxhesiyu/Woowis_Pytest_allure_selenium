from time import sleep
import pytest
import allure
from selenium.webdriver.common.by import By

from common.base import sel_end_keys, sel_click, refresh_when_element_appears, redirect_URL, \
    sel_hover, check_text_exists
from common.selenium_login import login_and_verify
from po.shopping import Shopping_querySku



@allure.title('用户获取不同赠品')
class TestFreeGift:

    @allure.title('用户获取不同促销')
    # 仅接收合并后的 fixture
    def test_shopping_FreeGift(self, open_page, merged_free_gift_fixture):
        with allure.step('获取合并后的测试数据（促销+账号密码）'):
            case_name = merged_free_gift_fixture["case_name"]
            skuTime = merged_free_gift_fixture["skuTime"]
            sku_list = merged_free_gift_fixture["sku_list"]
            expected_result = merged_free_gift_fixture["expected_result"]
            pcno = merged_free_gift_fixture["pcno"]
            password = merged_free_gift_fixture["password"]
            driver = open_page

        allure.dynamic.title(f"测试：{case_name}")

        # 核心：调用通用登录校验函数（复用登录用例的判断逻辑）
        with allure.step(f"登录并校验账号密码：{pcno}--{password}"):
            try:
                # 调用通用登录函数，登录失败会直接抛出异常，终止用例
                login_and_verify(driver, pcno, password)
            except Exception as e:
                # 登录失败时，标记用例失败并记录详细原因
                allure.attach(f"登录失败原因：{str(e)}", "登录校验结果", allure.attachment_type.TEXT)
                pytest.fail(f"促销用例[{case_name}]前置登录失败：{str(e)}")

        with allure.step("产品加入购物车判断促销"):
            allure.step("重定向页面")
            # 防止点数弹窗拦截把点击订购的按钮拦截掉
            sleep(1)
            refresh_when_element_appears(driver, (By.XPATH, "//span[contains(text(),'确定')]"),
                                         (By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]"))
            # 重定向URL
            redirect_URL(driver, "order/product",(By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]"))
            with allure.step("点击产品选项,进行产品加入购物车"):
                sel_click(driver, (By.XPATH, "//a[@class='top-link']//span[@class='zh'][contains(text(),'产品')]"))
            with allure.step("加购产品循环次数"):
                for i in range(skuTime):
                    Shopping_querySku(driver, sku_list)
            with allure.step("鼠标悬停在购物车元素上（不点击）"):
                sleep(1)
                sel_hover(driver, (By.XPATH, "//a[@class='item']//span[@class='zh'][contains(text(),'购物车')]"))
                sleep(1)  # 防止结算按钮出不来
            with allure.step("点击购物车的去结算按钮）"):
                sel_click(driver, (By.XPATH, "//span[contains(text(),'去结算(Go to pay)')]"))
                allure.step("全局查找预期结果")
                text_exists = check_text_exists(driver, expected_result)
                if text_exists:
                    # 文本存在 → 用例通过，记录日志到Allure
                    success_msg = f"✅ 用例[{case_name}]成功：预期文本「{expected_result}」存在于页面中"
                    print(success_msg)
                    allure.attach(success_msg, "结果验证", allure.attachment_type.TEXT)
                else:
                    # 文本不存在 → 标记用例失败（触发钩子自动截图）
                    fail_msg = f"❌ 用例[{case_name}]失败：预期文本「{expected_result}」不存在于页面中"
                    print(fail_msg)
                    # 可选：额外添加文本日志到Allure（截图由钩子自动完成）
                    allure.attach(fail_msg, "结果验证", allure.attachment_type.TEXT)
                    # 关键：调用pytest.fail标记用例失败，钩子会自动捕获失败状态并截图
                    pytest.fail(fail_msg)









