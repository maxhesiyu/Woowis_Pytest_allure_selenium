from appium import webdriver
from appium.options.android import UiAutomator2Options
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import time

# ========== 全局配置 ==========
TESSERACT_EXE_PATH = r"D:\OCR\tesseract.exe"
pytesseract.tesseract_cmd = TESSERACT_EXE_PATH

DEVICE_NAME = "AN6B024B01061442"
PLATFORM_VERSION = "16"

SCREENSHOT_DIR = "./ocr_click_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 坐标校准参数
X_OFFSET = 0
Y_OFFSET = 60


# ========== 工具函数 ==========
def get_device_resolution(driver):
    """获取设备真实分辨率"""
    try:
        width = driver.get_window_size()['width']
        height = driver.get_window_size()['height']
        print(f"✅ 设备分辨率：{width}×{height}")
        return (width, height)
    except:
        return (1280, 2800)  # 匹配你的截图分辨率


def preprocess_image(img_path):
    """轻量预处理：提升文字连贯性，不改变尺寸"""
    img = Image.open(img_path)
    return img


def ocr_get_text_coordinate(img_path, target_text):
    """优化识别逻辑：拼接连续文字块，匹配完整目标"""
    processed_img = preprocess_image(img_path)
    ocr_data = pytesseract.image_to_data(
        processed_img, lang='chi_sim', output_type=pytesseract.Output.DICT
    )

    # 方案1：拼接连续文字块，匹配完整目标
    text_blocks = []  # 存储(拼接文字, 合并后的坐标框)
    current_text = ""
    current_box = None  # [x1, y1, x2, y2]

    for i, text in enumerate(ocr_data['text']):
        clean_text = text.replace(" ", "").strip()
        if not clean_text:
            # 遇到空文字，结束当前块
            if current_text:
                text_blocks.append((current_text, current_box))
                current_text = ""
                current_box = None
            continue

        # 拼接当前文字，更新坐标框
        current_text += clean_text
        x1 = ocr_data['left'][i]
        y1 = ocr_data['top'][i]
        x2 = x1 + ocr_data['width'][i]
        y2 = y1 + ocr_data['height'][i]

        if not current_box:
            current_box = [x1, y1, x2, y2]
        else:
            # 合并坐标框（取最小x1/y1，最大x2/y2）
            current_box[0] = min(current_box[0], x1)
            current_box[1] = min(current_box[1], y1)
            current_box[2] = max(current_box[2], x2)
            current_box[3] = max(current_box[3], y2)

    # 处理最后一个文字块
    if current_text:
        text_blocks.append((current_text, current_box))

    # 遍历拼接后的文字块，匹配目标
    for text, box in text_blocks:
        if target_text in text:
            print(f"🔍 匹配到文字块：{text} | 坐标：{box}")
            return tuple(box)

    # 打印所有拼接后的文字块，便于调试
    all_blocks = " | ".join([f"{t}:{b}" for t, b in text_blocks])
    print(f"❌ 未匹配到「{target_text}」，拼接后的文字块：{all_blocks}")
    return None


def convert_coordinate(screenshot_box, screenshot_size, screen_size):
    """等比坐标转换+偏移补偿"""
    s_x1, s_y1, s_x2, s_y2 = screenshot_box
    s_w, s_h = screenshot_size
    scr_w, scr_h = screen_size

    scale_x = scr_w / s_w
    scale_y = scr_h / s_h

    center_x = int((s_x1 + s_x2) / 2 * scale_x) + X_OFFSET
    center_y = int((s_y1 + s_y2) / 2 * scale_y) + Y_OFFSET

    print(f"📐 缩放比例 X:{scale_x:.2f} Y:{scale_y:.2f}")
    print(f"🎯 最终点击坐标：({center_x},{center_y})")
    return (center_x, center_y)


def take_screenshot(driver, filename):
    """截图并获取分辨率"""
    path = os.path.join(SCREENSHOT_DIR, filename)
    driver.save_screenshot(path)
    with Image.open(path) as img:
        size = img.size
    print(f"📸 截图保存：{path}，截图分辨率：{size}")
    return path, size


def click_by_ocr(driver, target_text, shot_name):
    """识别+转换+点击一体化"""
    shot_path, shot_size = take_screenshot(driver, shot_name)
    screen_size = get_device_resolution(driver)
    box = ocr_get_text_coordinate(shot_path, target_text)
    if not box:
        return False
    click_pos = convert_coordinate(box, shot_size, screen_size)
    driver.tap([click_pos], 500)
    time.sleep(2)
    return True


def input_text_to_wechat(driver, text):
    """微信输入框输入文字（解决send_keys报错）"""
    try:
        # 方法1：定位微信输入框元素（通用xpath）
        input_box = driver.find_element(
            "xpath", '//*[@resource-id="com.tencent.mm:id/et_message"]'
        )
        input_box.send_keys(text)
        print(f"✅ 成功输入文字：{text}")
        return True
    except Exception as e:
        print(f"⚠️ 定位输入框失败，尝试模拟输入：{e}")
        # 方法2：模拟ADB输入（兜底方案）
        try:
            driver.execute_script('mobile: inputText', {'text': text})
            print(f"✅ 模拟输入文字：{text}")
            return True
        except:
            print("❌ 输入文字失败")
            return False


# ========== 测试主流程 ==========
def run_test():
    options = UiAutomator2Options()
    options.set_capability("deviceName", DEVICE_NAME)
    options.set_capability("platformVersion", PLATFORM_VERSION)
    options.set_capability("platformName", "Android")
    options.set_capability("appPackage", "com.tencent.mm")
    options.set_capability("appActivity", ".ui.LauncherUI")
    options.set_capability("noReset", True)
    options.set_capability("disableWindowAnimation", True)
    # 增加输入相关配置
    options.set_capability("unicodeKeyboard", True)
    options.set_capability("resetKeyboard", True)

    driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)
    driver.implicitly_wait(15)
    print("✅ Appium驱动初始化完成")

    try:
        # 等待聊天列表加载
        time.sleep(8)
        # 识别并点击文件传输助手
        if click_by_ocr(driver, "文件传输助手", "chat_list.png"):
            print("✅ 成功点击文件传输助手")
        else:
            # 兜底坐标（根据你的设备微调）
            driver.tap([(200, 400)], 500)
            print("⚠️ 使用兜底坐标点击文件传输助手")
        time.sleep(3)  # 等待聊天窗口加载

        # 点击输入框（通用坐标）
        input_box_coords = (300, 1100)
        driver.tap([input_box_coords], 500)
        print(f"✅ 点击输入框坐标：{input_box_coords}")
        time.sleep(1)

        # 输入测试文字（修复send_keys报错）
        input_text_to_wechat(driver, "坐标校准测试")
        time.sleep(1)

        # 识别并点击「发送」按钮
        if click_by_ocr(driver, "发送", "send_btn.png"):
            print("✅ 成功点击发送按钮")
        else:
            # 发送按钮兜底坐标
            send_btn_coords = (500, 1100)
            driver.tap([send_btn_coords], 500)
            print(f"⚠️ 使用兜底坐标点击发送按钮：{send_btn_coords}")

        print("\n🎉 测试完成！")
    except Exception as e:
        print(f"\n❌ 异常：{str(e)}")
        # 保存异常截图
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "error.png"))
        print(f"📸 异常截图已保存：{os.path.join(SCREENSHOT_DIR, 'error.png')}")
    finally:
        driver.quit()
        print("✅ 驱动已退出")


if __name__ == "__main__":
    run_test()