import allure
import pytest
import requests
import json

from config.path_config import get_excel_file_path
from common.read_from_excel import read_test_data_from_excel


class TestLogin:
    """登录接口测试类（仅提交Body并提取Token）"""

    @pytest.mark.parametrize(
        "case",
        read_test_data_from_excel(
            file_path=str(get_excel_file_path("Excel_API/接口登录参数化.xlsx")),
            sheet_name="Sheet2",
            parse_sku=False,
            sku_col_index=0
        )
    )
    @allure.title('{case[0]}')  # 动态显示表格中的用例名
    def test_api_login(self, case):
        """登录接口测试方法（保留，用于pytest测试）"""
        # 调用核心逻辑，复用代码
        self._get_token_from_login(case)

    # 新增：核心登录+提取Token逻辑（内部复用）
    def _get_token_from_login(self, case):
        case_name = case[0]
        url = case[1]
        method = case[2].upper()
        body_str = case[3]

        # 处理请求体
        try:
            body_dict = json.loads(body_str)
            payload = json.dumps(body_dict, ensure_ascii=False)
        except json.JSONDecodeError as e:
            pytest.fail(f"【{case_name}】请求体格式错误：{str(e)}")

        # 发送请求
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=payload,
                timeout=15
            )
            response_text = response.text
        except requests.exceptions.RequestException as e:
            pytest.fail(f"【{case_name}】请求发送失败：{str(e)}")

        # 提取Token
        try:
            resp_json = response.json()
            token = resp_json.get("data", {}).get("value", {}).get("UserToken")
            assert token is not None and token != "", f"【{case_name}】Token为空"
            allure.attach(token, f"{case_name} - 登录Token", allure.attachment_type.TEXT)
            print(f"🎉 【{case_name}】成功提取Token：{token}")
            return token  # 返回Token（供内部方法调用）
        except json.JSONDecodeError:
            pytest.fail(f"【{case_name}】响应不是JSON格式：{response_text}")
        except AssertionError as e:
            pytest.fail(str(e))

    # 新增：供外部调用的静态方法（核心！）
    @staticmethod
    def get_login_token():
        """独立获取登录Token（无pytest依赖，供订单接口调用）"""
        # 1. 读取登录Excel的Sheet2数据（正确账号）
        login_cases = read_test_data_from_excel(
            file_path=str(get_excel_file_path("Excel_API/接口登录参数化.xlsx")),
            sheet_name="Sheet2",
            parse_sku=False,
            sku_col_index=0
        )
        if not login_cases:
            raise RuntimeError("❌ 登录Excel的Sheet2无可用用例")

        # 2. 执行登录并提取Token（取第一个正确用例）
        login = TestLogin()
        token = login._get_token_from_login(login_cases[0])
        return token