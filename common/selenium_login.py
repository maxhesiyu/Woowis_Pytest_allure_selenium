from selenium.common import TimeoutException
from selenium.webdriver.common.by import By

from common.base import sel_click, check_text_exists
from common.log import log
from po.event import Myo_PcNo_Pwd



def login_and_verify(driver, pcno, password, timeout=5):

    """
    通用登录+登录成功校验函数（所有用例复用）
    :param driver: 浏览器驱动
    :param pcno: 顾客编号
    :param password: 密码
    :param timeout: 校验超时时间
    :return: 登录成功返回True，失败抛出异常
    """
    try:
        # 1. 输入账号密码（复用现有的Myo_PcNo_Pwd函数）
        Myo_PcNo_Pwd(driver, pcno, password)
        log.info(f"✅ 已输入账号密码：{pcno}--{password}")

        # 2. 点击登录
        sel_click(driver, (By.XPATH, "//span[contains(text(),'登录(Login)')]"))
        log.info(f"✅ 已点击登录按钮（账号：{pcno}）")

        # 3. 校验登录是否成功（核心：和登录用例的判断逻辑保持一致）
        # 1：检查登录后出现“退出登录”按钮，判断是否登录成功
        login_success = check_text_exists(driver, "退出登录", timeout=timeout)

        if login_success:
            log.info(f"✅ 账号{pcno}登录成功！")
            return True
        else:
            print(f"❌ 账号{pcno}登录失败：未检测到登录成功的标识,请检查账号密码是否正确")
            raise AssertionError(f"❌ 账号{pcno}登录失败：未检测到登录成功的标识")

    except TimeoutException:
        raise TimeoutException(f"❌ 账号{pcno}登录校验超时（{timeout}s），未检测到登录成功标识")
    except Exception as e:
        raise Exception(f"❌ 账号{pcno}登录异常：{str(e)}")


