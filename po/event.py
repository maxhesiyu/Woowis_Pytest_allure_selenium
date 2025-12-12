import pytest
from selenium.webdriver.common.by import By

from common.base import sel_end_keys, sel_click
from config.config import ENV



def myo_login(driver,url,name,password):
    driver = driver
    driver.get(url)
    driver.implicitly_wait(10)
    sel_end_keys(driver, (By.XPATH, "//input[@placeholder='顾客编号(PC ID)']"), name)
    sel_end_keys(driver, (By.XPATH, "//input[@placeholder='密码(Password)']"), password)
    sel_click(driver, (By.XPATH, "//span[contains(text(),'登录(Login)')]"))

