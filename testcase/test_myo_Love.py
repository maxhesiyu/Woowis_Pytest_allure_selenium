from time import sleep

import allure
from selenium.webdriver.common.by import By

from common.base import sel_end_keys, sel_click, sel_hover, get_text, refresh_when_element_appears, \
    assert_text_in_element


@allure.title('Myo_公益专区')
def test_Myo_Love_01(DengLu):
    driver = DengLu
    with allure.step("查看公益专区"):
        sleep(1)
        # 防止点数弹窗拦截把点击订购的按钮拦截掉
        refresh_when_element_appears(driver, (By.XPATH, "//span[contains(text(),'确定')]"),
                                     (By.XPATH, "//span[@class='main drop zh'][contains(text(),'公益专区')]"))
        sel_hover(driver,(By.XPATH,"//span[@class='main drop zh'][contains(text(),'公益专区')]"))
    with allure.step("进入我的携手关爱"):
        sel_click(driver,(By.XPATH,"//p[contains(text(),'我的携手关爱')]"))
        sleep(2)  # 暂停2秒，便于观察效果
        allure.story("查看捐赠图片")
        sel_click(driver,(By.XPATH,"//div[@class='content']//div[1]//div[1]//div[1]//div[2]//img[1]"))
        sleep(1)
        sel_click(driver,(By.XPATH,"//button[@class='right ivu-carousel-arrow ivu-carousel-arrow-always']"))
        sleep(1)
        sel_click(driver,(By.XPATH,"//i[@class='ivu-icon ivu-icon-close-circled']"))
    with allure.step("切换公益专区年度"):
        sel_click(driver, (By.XPATH, "//i[@class='ivu-icon ivu-icon-arrow-down-b ivu-select-arrow']"))
        sleep(0.5)
        sel_click(driver, (By.XPATH, "//li[normalize-space()='2025']"))
    with allure.step("切换至申请玫瑰使者"):
        sel_hover(driver,(By.XPATH,"//span[@class='main drop zh'][contains(text(),'公益专区')]"))
        sel_click(driver,(By.XPATH,"//p[contains(text(),'申请成为玫瑰使者')]"))
        sleep(2)
        allure.story("追加你的爱心")
        sel_click(driver,(By.XPATH,"//div[@class='append-donation']"))
        allure.story("断言限制服务费捐赠仅企业客户")
        sleep(1)
        sel_click(driver,(By.XPATH,"//label[contains(text(),'服务费代扣捐赠(Service fee donation)')]"))
        sleep(1)
        assert_text_in_element(driver,
                               (By.XPATH,"//div[contains(text(),'服务费代扣仅限企业客户')]"),
                               "服务费代扣仅限企业客户")
        sel_click(driver,(By.XPATH,"//div[@class='ivu-modal-confirm-footer']//span[contains(text(),'确定')]"))
        sleep(1)
    with allure.step("自行转账捐赠"):
        sel_click(driver, (By.XPATH, "//label[contains(text(),'自行转账捐赠(Direct donation)')]"))
        sel_click(driver, (By.XPATH, "//i[@class='ivu-icon ivu-icon-arrow-down-b ivu-select-arrow']"))
        sleep(1)
        sel_click(driver, (By.XPATH, "//div[@class='container']//li[2]"))
        sleep(0.5)
        sel_click(driver, (By.XPATH, "//span[contains(text(),'提交')]"))
        sleep(1)
        sel_click(driver, (By.XPATH, "//div[@class='ivu-modal-confirm-footer']//span[contains(text(),'确定')]"))
        sleep(1)
        sel_click(driver, (By.XPATH, "//div[@class='ivu-modal-confirm-footer']//span[contains(text(),'确定')]"))








