from time import sleep
import allure
from selenium.webdriver.common.by import By
from common.base import sel_end_keys, sel_click, refresh_when_element_appears


def myo_login(driver,url,name,password):
    driver = driver
    driver.get(url)
    driver.implicitly_wait(10)
    sel_end_keys(driver, (By.XPATH, "//input[@placeholder='顾客编号(PC ID)']"), name)
    sel_end_keys(driver, (By.XPATH, "//input[@placeholder='密码(Password)']"), password)
    sel_click(driver, (By.XPATH, "//span[contains(text(),'登录(Login)')]"))


def ZhuCe(driver,randomPhone,CAPTCHA,referrer,name,npwd,ncpwd,randomSFZ):
    with allure.step("注册PC用户"):
        driver = driver
        allure.dynamic.title("注册基本流程")
        sel_click(driver, (By.XPATH, "//span[contains(text(),'点击注册(Click To Register)')]"))
        sel_click(driver, (By.XPATH, "//div[contains(text(),'申请优惠顾客')]"))
        allure.dynamic.title("弹窗同意注册提示")
        # 弹窗同意注册提示
        sel_click(driver, (By.XPATH, "//span[contains(text(),'我理解并同意以下全部内容')]"))
        sel_click(driver, (By.XPATH, "//button[@class='button confirm ivu-btn ivu-btn-primary']"))
        allure.dynamic.title("手机号填写")
        sel_end_keys(driver, (By.XPATH,
                              "//body/div[@id='app']/div[@class='root-content']/div[@id='root']/div[@class='container createAccount']/div[@class='content']/section/form[@class='ivu-form ivu-form-label-top']/div[@class='c-form-item ivu-form-item ivu-form-item-required']/div[@class='ivu-form-item-content']/div[@class='ivu-input-wrapper ivu-input-wrapper-large ivu-input-type']/input[1]"),
                     randomPhone)
        allure.dynamic.title("验证码填写")
        sel_end_keys(driver, (By.XPATH, "//div[@class='yzmInput ivu-col ivu-col-span-11']//input[@type='text']"),
                     CAPTCHA)
        allure.dynamic.title("朋友号填写")
        sel_click(driver, (By.XPATH, "//label[contains(text(),'朋友(Friend)')]"))
        sel_end_keys(driver, (By.XPATH, "//input[@placeholder='顾客编号(PC ID)']"), referrer)
        sleep(1)
        allure.dynamic.title("验证朋友号")
        sel_click(driver, (By.XPATH, "//span[contains(text(),'验证顾客编号(Verify the PC ID)')]"))
        sel_click(driver, (By.XPATH, "//div[contains(@class,'bottom-button button1')]//button[2]"))
        allure.dynamic.title("个人信息填写")
        sleep(1)
        allure.dynamic.title("姓名填写")
        sel_end_keys(driver, (By.XPATH, "//input[@placeholder='请填写真实姓名 (Please fill in the legal name)']"),
                     name)
        allure.dynamic.title("密码填写")
        sel_end_keys(driver, (By.XPATH,
                              "//div[@class='passwordlabel ivu-form-item ivu-form-item-required']//input[@type='password']"),
                     npwd)
        sel_end_keys(driver,
                     (By.XPATH, "//div[@class='ivu-form-item ivu-form-item-required']//input[@type='password']"),
                     ncpwd)
        allure.dynamic.title("国外身份证填写")
        sleep(2)
        sel_click(driver, (By.XPATH, "//label[contains(text(),'其它国籍（地区）身份证件')]"))
        sel_end_keys(driver, (By.XPATH,
                              "//div[@class='ivu-form-item']//div[@class='ivu-input-wrapper ivu-input-wrapper-large ivu-input-type']//input[@type='text']"),
                     randomSFZ)
        allure.dynamic.title("日历选择日期")
        # 直接通过JS查找所有日期输入框，设置值（适配任意定位）
        driver.execute_script("""
            // 查找包含生日/生日相关的input（按placeholder/name匹配）
            const birthdayInputs = document.querySelectorAll('input[placeholder*="生日"], input[name*="birthday"], .selectbirthday input');
            if (birthdayInputs.length > 0) {
                birthdayInputs[0].removeAttribute('readonly');
                birthdayInputs[0].value = '2005-06-17';
                birthdayInputs[0].dispatchEvent(new Event('change'));
            }
        """)
        allure.dynamic.title("勾选优惠顾客政策并点击申请优惠注册按钮")
        sleep(1)
        sel_click(driver, (By.XPATH, "//a[contains(text(),'优惠顾客政策(Preferential customer policy)')]"))
        sleep(1)
        sel_click(driver, (By.XPATH, "//button[@class='goon-btn ivu-btn ivu-btn-primary ivu-btn-large']"))
        sel_click(driver, (By.XPATH, "//button[@class='gobtn ivu-btn ivu-btn-primary ivu-btn-large']"))
        sel_click(driver, (By.XPATH, "//span[contains(text(),'开始购物')]"))
        refresh_when_element_appears(driver, (By.XPATH, "//i[@class='ivu-icon ivu-icon-ios-close-circle-outline']"),
                                     (By.XPATH, "//input[@placeholder='搜索(Search)']"))

