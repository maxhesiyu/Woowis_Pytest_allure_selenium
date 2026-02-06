import os
import random
import string
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 路径配置
TEST_CASE_DIR = PROJECT_ROOT / "testtcase/test_shopping_FreeGift.py"   #需要执行pytest的文件路径
# EXCEL_FILE_PATH = PROJECT_ROOT / "测试登录参数化.xlsx"
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

# 测试环境参数配置
class ENV:
    URL = "https://cvoqa.doterra.cn/vo/index.html#/home"   #测试环境订购网址
    pcno = "60003154"  #默认账号
    password = "123"   #默认密码
    phone = "13345238446"  #固定手机号
    CAPTCHA = "1065"  #验证码
    referrer = "2"  #注册推荐人
    # 注册个人信息默认数据
    name = "max何测试"   #姓名
    npwd = "a1234567"  #密码
    ncpwd = "a1234567"  #确认密码
    SKU = ["30112012","30122012"]  #产品的添加
    SKUTime = 8  #产品加购循环次数
    # 尊享购sku:"60206026"
    address = "联系人:测试,收货地址,广东省广州市白云区太和镇我的街道测试地址不发货"
 # ========== 核心：动态生成随机手机号 ==========
    @staticmethod
    def generate_random_phone():
        """生成随机合法手机号（每次调用生成新值）"""
        prefix_list = ["138", "139", "156", "186", "177"]
        prefix = random.choice(prefix_list)
        suffix = ''.join(random.choices('0123456789', k=8))
        return prefix + suffix

    # 生成随机手机号
    @property
    def randomPhone(self):
        return self.generate_random_phone()

    # 同理：随机身份证号每次刷新
    # 随机国外身份证字符
    @staticmethod
    def generate_random_sfz():
        """生成随机身份证号（示例，可根据实际规则优化）"""
        random_suffix = ''.join(random.choices('0123456789abcdefghijklmiopqzx', k=13))
        return  random_suffix

    @property
    def randomSFZ(self):
        return self.generate_random_sfz()

# 实例化ENV类（全局使用）
env = ENV()

# 测试小样
if __name__ == "__main__":
    var = ENV().randomSFZ
    print(var)

# 创建必要目录
for dir_path in [LOG_DIR, ALLURE_IMG_DIR, ALLURE_RESULTS]:
    if not dir_path.exists():
        os.makedirs(dir_path)