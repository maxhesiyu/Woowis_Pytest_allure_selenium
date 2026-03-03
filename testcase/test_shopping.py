from time import sleep

import allure
from selenium.webdriver.common.by import By

from common.base import refresh_when_element_appears, redirect_URL
from config.config import env, ENV
from po.event import ZhuCe
from po.shopping import Shopping_product_Order


@allure.title('用户下单流程')
def test_shopping_01(DengLu):
    with allure.step("用户下单流程"):
        driver = DengLu
        allure.dynamic.title("用户下单流程")
        sleep(1)
        # 防止点数弹窗拦截把点击订购的按钮拦截掉
        refresh_when_element_appears(driver, (By.XPATH, "//span[contains(text(),'确定')]"),
                                 (By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]"))
        # 重定向URL
        redirect_URL(driver, "order/product",(By.XPATH, "//span[@class='main zh'][contains(text(),'在线订购')]"))
        # 3. 重定向后操作元素,调用封装的商品列表页开始到付款流程
        Shopping_product_Order(driver, ENV.SKUTime, ENV.SKU, False, ENV.address)



@allure.title('用户注册流程')
def test_ZhuCe_01(self,open_page):
    with allure.step("用户注册流程"):
        driver = open_page
        allure.dynamic.title("用户注册流程")
        ZhuCe(driver,env.randomPhone,ENV.CAPTCHA,ENV.referrer,ENV.name,ENV.npwd,ENV.ncpwd,env.randomSFZ)



# 注册流程和加购产品到下单方法组合成流程
@allure.title('用户注册到下单')
def test_zhuCeOrder(open_page):
    with allure.step("用户注册到下单流程"):
        driver = open_page
        allure.dynamic.title("用户注册到下单流程")
        ZhuCe(driver,env.randomPhone,ENV.CAPTCHA,ENV.referrer,ENV.name,ENV.npwd,ENV.ncpwd,env.randomSFZ)
        sleep(2)
        Shopping_product_Order(driver, ENV.SKUTime, ENV.SKU, True, ENV.address)