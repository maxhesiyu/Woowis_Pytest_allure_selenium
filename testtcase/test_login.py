from time import sleep


from common.base import get_all_visible_text
from common.log import log
from config.config import ENV, env
from po.event import ZhuCe, Myo_PcNo_Pwd, Myo_Login_btn
import allure


# ========== 测试类（无定位符，全局文本断言） ==========
class TestLogin:

    @allure.story('登录测试（全局文本断言')
    def test_login(self, open_page, merged_login_fixture):
        """登录用例：复用合并后的Fixture，1套登录数据对应1套账号密码"""
        # 从合并后的Fixture中一键读取所有数据（无需分开解析）
        case_name = merged_login_fixture["case_name"]
        expected_result = merged_login_fixture["expected_result"]
        pcno = merged_login_fixture["pcno"]
        password = merged_login_fixture["password"]
        driver = open_page

        allure.dynamic.title(f"用例名：{case_name}（账号：{pcno}）")
        log.info(f"📌 执行用例：{case_name}，账号：{pcno}，预期结果：{expected_result}")

        try:
            # 步骤1：输入账号密码
            with allure.step(f"输入顾客编号及密码: {pcno}--{password}"):
                Myo_PcNo_Pwd(driver,pcno,password)

            # 步骤2：点击登录 + 等待页面跳转（核心优化）
            with allure.step("点击登录按钮并等待页面跳转"):
                # 记录登录前的URL
                original_url = driver.current_url
                # 点击登录按钮
                Myo_Login_btn(driver)

            # 判断页面URL是否发生变化，发生变化留出3秒的等待页面渲染时间
            with allure.step("判断URL是否发生变化"):
                sleep(0.5)
                # 记录登录后的URL
                current_url = driver.current_url
                if current_url != original_url:
                    # URL变更 → 延迟3秒，给新页面渲染文本
                    log.info(f"✅ URL已变更：{original_url} → {current_url}，延迟2秒等待渲染")
                    sleep(2)
                else:
                    # URL未变更 → 立即执行判断，不延迟
                    log.warning(f"⚠️ URL未变更，仍停留在：{original_url}，立即执行判断")

            # ========== 核心：全局文本扫描 + 断言 ==========
            with allure.step("抓取页面所有可见文本（含弹窗）并断言预期结果"):
                # 抓取全页面文本（包括弹窗）
                all_page_text = get_all_visible_text(driver)
                # 模糊断言查找
                assert any(expected_result in text for text in all_page_text), \
                    f"断言失败！未找到包含「{expected_result}」的文本。页面文本：{all_page_text}"

        except Exception as e:
            # 失败时附加截图+全局文本，便于排查
            with allure.step("用例执行失败，附加截图和页面文本"):
                allure.attach(
                    driver.get_screenshot_as_png(),
                    f"失败截图：{case_name}",
                    allure.attachment_type.PNG
                )
                # 附加页面所有文本，方便排查
                all_page_text = get_all_visible_text(driver)
                allure.attach(
                    f"页面所有文本：{all_page_text}",
                    f"页面文本：{case_name}",
                    allure.attachment_type.TEXT
                )
            log.error(f"❌ 用例「{case_name}」执行失败：{str(e)}")
            raise











