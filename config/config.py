import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 路径配置
TEST_CASE_DIR = PROJECT_ROOT / "testtcase"
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
    URL = "https://cvoqa.doterra.cn/vo/index.html#/home"
    name = "60003152"  # 与Excel中密码正确账号一致
    password = "123"

# 创建必要目录
for dir_path in [LOG_DIR, ALLURE_IMG_DIR, ALLURE_RESULTS]:
    if not dir_path.exists():
        os.makedirs(dir_path)