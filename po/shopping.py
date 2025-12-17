from time import sleep

import allure
from selenium.webdriver.common.by import By

from common.base import sel_end_keys, sel_click, sel_hover


@allure.story('产品加购循环')
def Shopping_querySku(driver,sku):
    for idx, item in enumerate(sku):
        sleep(0.3)  #防止操作过快，查询按钮没有点击到
        sel_end_keys(driver, (By.XPATH, "//input[@placeholder='搜索(Search)']"), item)
        sel_click(driver, (By.XPATH, "//i[@class='ivu-icon ivu-icon-ios-search ivu-input-icon ivu-input-icon-normal']"))
        sel_click(driver, (By.XPATH, "//div[@type='default']"))

@allure.story('结算购物车产品')
def Shopping_downOrder(driver):
   with allure.step("鼠标悬停在购物车元素上（不点击）"):
        sel_hover(driver,(By.XPATH, "//a[@class='item']//span[@class='zh'][contains(text(),'购物车')]"))
   with allure.step("点击购物车的去结算按钮）"):
        sel_click(driver, (By.XPATH, "//span[contains(text(),'去结算(Go to pay)')]"))
   with allure.step("点击购物车的去结算按钮到支付页面）"):
        sel_click(driver,(By.XPATH, "//span[contains(text(),'进行结账')]"))
        sel_click(driver,(By.XPATH, "//span[contains(text(),'提交订单')]"))
        sel_click(driver,(By.XPATH, "//span[contains(text(),'去支付')]"))