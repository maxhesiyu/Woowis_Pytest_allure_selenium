import os
import random
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 路径配置
TEST_CASE_DIR = PROJECT_ROOT / "testtcase/test_otg.py"   #需要执行pytest的文件路径
EXCEL_FILE_PATH = PROJECT_ROOT / "测试登录参数化.xlsx"
LOG_DIR = PROJECT_ROOT / "log"
ALLURE_RESULTS = PROJECT_ROOT / "allure-results"
ALLURE_HTML = PROJECT_ROOT / "allure-report"
ALLURE_IMG_DIR = LOG_DIR / "image_allure"

# 邮箱配置
EMAIL_CONFIG = {
    "sender": "hesy@sh.woowis.com",
    "password": "mMhohPcdkS2zAhup",
    "host": "smtp.exmail.qq.com",
    "port": 465,
    "receivers": ["2847795529@qq.com"],
}

# 测试环境配置（统一账号，解决元素定位失败）
class ENV:
    URL = "https://cvoqa.doterra.cn/vo/index.html#/home"   #测试环境订购网址
    pcno = "60003156"  #默认账号
    password = "123"   #默认密码
    phone = "13345238446"  #固定手机号
    randomPhone = f"133{''.join(random.choices('0123456789', k=8))}"   #生成随机手机号
    CAPTCHA = "1065"  #验证码
    referrer = "2"  #注册推荐人
    # 注册个人信息默认数据
    name = "max测试"   #姓名
    npwd = "a1234567"  #密码
    ncpwd = "a1234567"  #确认密码
    randomSFZ = f"a{''.join(random.choices('0123456789abcdefghijklmiopqzx', k=13))}"  #随机国外身份证字符
    BOGOSKU = ["60204923","60211851","60211850"]  #bogo产品的诉苦
    BOGOSKUTime = 1  #循环次数
    尊享购sku = "60206026"


# 测试小样
if __name__ == "__main__":
    var = ENV().randomSFZ
    print(var)

# 创建必要目录
for dir_path in [LOG_DIR, ALLURE_IMG_DIR, ALLURE_RESULTS]:
    if not dir_path.exists():
        os.makedirs(dir_path)