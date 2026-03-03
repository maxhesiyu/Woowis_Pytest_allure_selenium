from time import sleep
import pytest
import allure
from selenium.webdriver.common.by import By

from common.base import sel_click, get_all_visible_text
from common.log import log
from config.config import ENV, env
from config.excel_config import EXCEL_PATHS, EXCEL_READ_CONFIG, EXCEL_MERGE_CONFIG  # 导入配置
from common.read_excel_pandas import ExcelHandler
from po.event import ZhuCe, Myo_PcNo_Pwd, Myo_Login_btn


# ====================== 测试数据加载（基于配置文件） ======================
def load_login_test_data():
    """加载登录测试数据（封装为函数，便于复用/调试）"""
    # 构建Excel合并配置列表（根据登录场景调整配置key）
    excel_config_list = [
        {
            "file_path": EXCEL_PATHS["account"],
            **EXCEL_READ_CONFIG["login"]["account"]  # 注意：需在excel_config.py中配置login节点
        },
        {
            "file_path": EXCEL_PATHS["login_case"],  # 注意：需在excel_config.py中添加login_case路径
            **EXCEL_READ_CONFIG["login"]["case_info"]
        }
    ]
    # 读取登录场景的合并配置
    merge_config = EXCEL_MERGE_CONFIG["login"]

    try:
        merged_df = ExcelHandler.merge_excel(
            excel_config_list=excel_config_list,
            key_column=merge_config["key_column"],
            merge_how=merge_config["merge_how"],
            preserve_all_fields=merge_config["preserve_all_fields"]
        )
        # 可选：打印数据详情（调试用）
        # ExcelHandler.print_data_detail(merged_df)
        test_data_list = merged_df.to_dict('records')
        log.info(f"✅ 登录测试数据加载成功，共{len(test_data_list)}条")
        return test_data_list
    except Exception as e:
        log.error(f"❌ 登录测试数据加载失败：{str(e)}")
        raise


# 加载测试数据
MERGED_LOGIN_DATA = load_login_test_data()


# ====================== 测试用例逻辑 ======================
@allure.title('登录测试（全局文本断言）')
class TestLogin:

    @pytest.mark.parametrize("test_data", MERGED_LOGIN_DATA)
    @allure.title('登录场景：{test_data[场景]}')
    def test_login(self, open_page, test_data):
        """登录用例：复用合并后的Excel数据，1套登录数据对应1套账号密码"""
        # 1. 读取测试数据（解构赋值，更清晰）
        case_id = test_data.get("序号")
        case_name = test_data["场景"]
        pcno = test_data["账号"]
        password = test_data["密码"]
        expected_result = test_data["预期结果"]
        driver = open_page

        # 2. 空值提示（优化日志和allure附件）
        empty_hints = []
        if not pcno:
            empty_hints.append("账号为空")
            log.warning(f"用例[{case_id}-{case_name}]账号为空，将使用空值执行登录")
        if not password:
            empty_hints.append("密码为空")
            log.warning(f"用例[{case_id}-{case_name}]密码为空，将使用空值执行登录")

        # 动态更新用例标题
        empty_mark = f"【{','.join(empty_hints)}】" if empty_hints else ""
        allure.dynamic.title(f"{case_name}（序号：{case_id}）{empty_mark}")
        if empty_hints:
            allure.attach(f"⚠️ {','.join(empty_hints)}，将使用空值执行登录", "数据提示", allure.attachment_type.TEXT)

        log.info(f"📌 执行用例：{case_name}，账号：{pcno}，预期结果：{expected_result}")

        try:
            # 步骤1：输入账号密码
            with allure.step(f"输入顾客编号及密码: {pcno}--{password}"):
                Myo_PcNo_Pwd(driver, pcno, password)

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
            with allure.step(f"抓取页面所有可见文本并断言预期结果：{expected_result}"):
                # 抓取全页面文本（包括弹窗）
                all_page_text = get_all_visible_text(driver)

                # 验证预期结果
                if any(expected_result in text for text in all_page_text):
                    success_msg = f"✅ 用例[{case_id}-{case_name}]验证通过：预期文本「{expected_result}」存在"
                    allure.attach(success_msg, "验证结果")
                    log.info(success_msg)
                else:
                    fail_msg = f"❌ 用例[{case_id}-{case_name}]验证失败：未找到包含「{expected_result}」的文本。页面文本：{all_page_text}"
                    allure.attach(fail_msg, "验证结果")
                    # 失败时附加截图
                    allure.attach(
                        driver.get_screenshot_as_png(),
                        f"失败截图：{case_name}",
                        allure.attachment_type.PNG
                    )
                    # 附加页面所有文本，方便排查
                    allure.attach(
                        f"页面所有文本：{all_page_text}",
                        f"页面文本：{case_name}",
                        allure.attachment_type.TEXT
                    )
                    pytest.fail(fail_msg)

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
            error_msg = f"❌ 用例[{case_id}-{case_name}]执行失败：{str(e)}"
            log.error(error_msg)
            pytest.fail(error_msg)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--alluredir", "./allure-results"])