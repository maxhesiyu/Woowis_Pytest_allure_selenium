import time
from time import sleep

import allure
from selenium.webdriver.common.by import By

from common.base import sel_end_keys, sel_click, sel_hover, get_text


@allure.story('商品列表页开始到付款流程')
def Shopping_product_Order( driver, sku_time, sku,ads,address):
    """
        函数功能：商品下单
        :param driver: 浏览器驱动
        :param sku_time: SKU时间参数（ENV.SKUTime）
        :param sku: SKU列表（ENV.SKU）
        :param ads: 布偶值，true执行新增地址操作，false不执行
        :param address: 新增的地址信息参数
    """
    with allure.step("点击产品选项,进行产品加入购物车"):
        sel_click(driver, (By.XPATH, "//a[@class='top-link']//span[@class='zh'][contains(text(),'产品')]"))
    with allure.step("自定义加购循环次数"):
        for i in range(sku_time):
            Shopping_querySku(driver, sku)
    with allure.step("导入结算流程方法"):
        Shopping_downOrder(driver,ads,address)



@allure.story('产品加购循环')
def Shopping_querySku(driver, sku):
    for idx, item in enumerate(sku):
        sleep(0.3)  #防止操作过快，查询按钮没有点击到
        sel_end_keys(driver, (By.XPATH, "//input[@placeholder='搜索(Search)']"), item)
        sel_click(driver, (By.XPATH, "//i[@class='ivu-icon ivu-icon-ios-search ivu-input-icon ivu-input-icon-normal']"))
        sel_click(driver, (By.XPATH, "//div[@type='default']"))


@allure.story('结算购物车产品')
def Shopping_downOrder(driver,ads,address):
    with allure.step("鼠标悬停在购物车元素上（不点击）"):
        sleep(1)
        sel_hover(driver, (By.XPATH, "//a[@class='item']//span[@class='zh'][contains(text(),'购物车')]"))
        sleep(1)  # 防止结算按钮出不来
    with allure.step("点击购物车的去结算按钮）"):
        sel_click(driver, (By.XPATH, "//span[contains(text(),'去结算(Go to pay)')]"))
    with allure.step("点击购物车的进行结账按钮到支付页面）"):
        sel_click(driver, (By.XPATH, "//span[contains(text(),'进行结账')]"))
        if ads:
            sel_click(driver, (By.XPATH, "//span[contains(text(),'放弃机会(Give up)')]"))
            sel_click(driver, (By.XPATH, "//span[contains(text(),'添加收货地址(Add address)')]"))
            allure.story("添加地址")
            Shopping_address_Recognize(driver,address)
            sleep(0.3)
            sel_click(driver, (By.XPATH, "//span[contains(text(),'进行结账')]"))
            sel_click(driver, (By.XPATH, "//span[contains(text(),'放弃机会(Give up)')]"))
        sel_click(driver, (By.XPATH, "//span[contains(text(),'提交订单')]"))
        sleep(1)
        sel_click(driver, (By.XPATH, "//span[contains(text(),'去支付')]"))



@allure.story('手动拉取输入框新增收货地址')
def Shopping_address_ManOpen(driver,addressName,address):
    sel_end_keys(driver, (By.XPATH, "//input[@placeholder='你的名字(Your Name)']"), addressName)
    sel_click(driver, (By.XPATH, "//span[contains(text(),'请选择省份(Province)')]"))
    sel_click(driver, (By.XPATH, "//li[contains(text(),'广东')]"))
    sel_click(driver, (By.XPATH, "//span[contains(text(),'请选择城市(City)')]"))
    sel_click(driver, (By.XPATH, "//li[contains(text(),'广州市')]"))
    sel_click(driver, (By.XPATH, "//span[@class='ivu-select-placeholder']"))
    sel_click(driver, (By.XPATH, "//li[contains(text(),'白云区')]"))
    sel_click(driver, (By.XPATH, "//input[@placeholder='请选择乡镇(Town)']"))
    sel_click(driver, (By.XPATH, "//li[contains(text(),'太和镇')]"))
    sel_end_keys(driver, (By.XPATH, "//input[@placeholder='请填写具体地址(Street address)']"),address)
    sel_click(driver, (By.XPATH, "//span[contains(text(),'确认(Confirm)')]"))

@allure.story('自动识别地址信息来新增收货地址')
def Shopping_address_Recognize(driver,address):
    sel_end_keys(driver,(By.XPATH, "//input[@placeholder='粘贴地址信息，自动拆分姓名、电话和地址']"),address)
    sel_click(driver,(By.XPATH, "//span[contains(text(),'识别')]"))
    sleep(6)
    getName = get_text(driver,(By.XPATH, "//input[@placeholder='你的名字(Your Name)']"))
    if getName == "":
        sleep(4)
    sel_click(driver, (By.XPATH, "//span[contains(text(),'确认(Confirm)')]"))
    sleep(2)