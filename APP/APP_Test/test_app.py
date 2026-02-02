from time import sleep

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# 1. 构建Android Options实例，配置原desired_caps参数
options = UiAutomator2Options()
# 核心配置（根据你的实际设备/应用修改）
options.set_capability("platformName", "Android")
options.set_capability("platformVersion", "16")  # 你的Android系统版本
options.set_capability("deviceName", "荣耀magic7 Pro")  # 你的设备名/模拟器名
options.set_capability("appPackage", "com.doterra.app")  # 被测APP包名
options.set_capability("appActivity", ".MainActivity")  # 被测APP启动页Activity
options.set_capability("noReset", True)  # 可选：不重置APP数据
options.set_capability("unicodeKeyboard", True)  # 可选：支持中文输入

# 2. 初始化driver，必须传入options关键字参数
driver = webdriver.Remote(
    command_executor="http://127.0.0.1:4723/wd/hub",
    options=options  # 强制要求的关键字参数
)

# # 简单操作：等待5秒（让App完全启动），然后关闭App
time.sleep(5)
element = driver.find_element(By.XPATH, "//*[@text='我的']")
element.click()
sleep(2)
element = driver.find_element(By.XPATH, "//*[@text='顾客编号']")
element.send_keys("60003156")
sleep(2)
element = driver.find_element(By.XPATH, "//*[@text='密码']")
element.send_keys("123")
sleep(2)
element = driver.find_element(By.XPATH, "//*[@text='登录']")
element.click()
# driver.find_element(AppiumBy.ACCESSIBILITY_ID, "我的").click()



driver.quit()

print("第一个Appium脚本运行成功！")