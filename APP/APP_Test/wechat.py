from appium import webdriver
from appium.options.android import UiAutomator2Options
import random
import time
import os

options = UiAutomator2Options()

options.set_capability("msedgedriverExecutable", r"D:\webdriver/msedgedriver.exe")
# 基础设备/应用配置
options.set_capability("deviceName", "Android设备")
options.set_capability("platformName", "Android")
options.set_capability("platformVersion", "16")
options.set_capability("appPackage", "com.tencent.mm")
options.set_capability("appActivity", ".ui.LauncherUI")
# 反检测核心配置
options.set_capability("noReset", True)  # 保留登录状态
options.set_capability("dontStopAppOnReset", True)
options.set_capability("skipDeviceInitialization", True)
options.set_capability("disableWindowAnimation", True)
# WebView 调试配置
options.set_capability("chromeOptions", {"androidProcess": "com.tencent.mm:appbrand0"})  # 小程序进程
options.set_capability("showChromedriverLog", True)  # 打印 ChromeDriver 日志（便于调试）
# 中文输入
options.set_capability("unicodeKeyboard", True)
options.set_capability("resetKeyboard", True)

# 连接 Appium Server
driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)
driver.implicitly_wait(20)  # 延长等待（WebView 加载慢）

# 步骤1：跳过登录，进入微信主界面
def skip_login(driver):
    try:
        driver.find_element("xpath", '//*[@text="我"]').click()
        driver.back()  # 返回主界面
        print("✅ 已跳过登录")
    except:
        print("⚠️  请手动登录微信，10秒后继续...")
        time.sleep(10)

skip_login(driver)

# 步骤2：打开「通讯录 → 公众号」
driver.find_element("xpath", '//*[@content-desc="通讯录"]').click()
time.sleep(2)
# 定位「公众号」入口（新版微信适配）
driver.find_element("xpath", '//*[@text="公众号"]').click()
time.sleep(2)

# 步骤3：搜索目标公众号（示例：微信公开课）
driver.find_element("xpath", '//*[@resource-id="com.tencent.mm:id/cn1"]/android.widget.EditText').click()
driver.find_element("xpath", '//*[@resource-id="com.tencent.mm:id/cn1"]/android.widget.EditText').send_keys("微信公开课")
time.sleep(2)
# 点击搜索结果
driver.find_element("xpath", '//*[@text="微信公开课"]').click()
time.sleep(3)

# 步骤4：切换到 WebView 上下文（核心！脱离原生）
# 打印所有上下文（原生+WebView）
contexts = driver.contexts
print(f"所有上下文：{contexts}")
# 切换到第一个 WebView 上下文（公众号 H5）
webview_context = [ctx for ctx in contexts if "WEBVIEW" in ctx][0]
driver.switch_to.context(webview_context)
print(f"✅ 已切换到 WebView 上下文：{webview_context}")

# 步骤5：定位公众号 H5 元素（Chrome DevTools 调试获取）
# 示例：点击公众号「菜单 → 文章」
# （需用 Chrome DevTools 抓取实际元素定位符，以下为示例）
driver.find_element("css selector", "#menu_1 > a").click()
time.sleep(3)

# 步骤6：验证文章标题（断言）
article_title = driver.find_element("xpath", '//h1[@class="rich_media_title"]').text
assert "微信" in article_title, f"❌ 未找到目标文章，标题：{article_title}"
print(f"✅ 公众号操作成功，文章标题：{article_title}")

# 步骤7：切回原生上下文（如需继续操作微信原生界面）
driver.switch_to.context(contexts[0])