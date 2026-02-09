import allure
import json
import pytest
import requests
from urllib.parse import urlencode  # 处理URL参数编码

from API.api_common.api_base import TestLogin  # 确保路径正确
from config.path_config import get_excel_file_path
from config.read_from_excel import read_test_data_from_excel


class TestOrder:  # 类名规范：大驼峰
    """提交订单接口测试类"""

    @pytest.mark.parametrize(
        "case",
        read_test_data_from_excel(
            file_path=str(get_excel_file_path("接口提交订单.xlsx")),
            sheet_name="Sheet1",
            parse_sku=False,
            sku_col_index=0
        )
    )
    @allure.title('{case[0]}')  # 动态显示订单用例名
    def test_submit_order(self, case):
        """提交订单接口：自动获取登录Token并拼接URL"""
        # 1. 提取订单用例数据
        case_name = case[0]
        base_url = case[1]
        method = case[2].upper()
        body_str = case[3]
        expected_http_code = case[4]
        # expected_value_json = case[5]  # 无需校验可注释

        # 2. 核心：调用TestLogin获取Token（一行代码搞定）
        try:
            token = TestLogin.get_login_token()  # 调用静态方法
            print(f"\n【{case_name}】获取到登录Token：{token}")
        except RuntimeError as e:
            pytest.fail(f"【{case_name}】获取Token失败：{str(e)}")

        # 3. 拼接订单URL（处理参数编码，避免特殊字符问题）
        url_params = {
            "token": token,
            "m": "og010",
            "channel": "MyO"
        }
        encoded_params = urlencode(url_params)  # 编码参数（关键！）
        # 避免URL重复拼接?
        if "?" in base_url:
            order_url = f"{base_url}&{encoded_params}"
        else:
            order_url = f"{base_url}?{encoded_params}"
        print(f"【{case_name}】拼接后URL：{order_url}")

        # 4. 处理订单请求体
        with allure.step("处理订单请求体"):
            try:
                body_dict = json.loads(body_str) if body_str.strip() else {}
                payload = json.dumps(body_dict, ensure_ascii=False)
                allure.attach(payload, f"{case_name} - 请求体", allure.attachment_type.JSON)
                print(f"【{case_name}】订单请求体：{payload}")
            except json.JSONDecodeError as e:
                pytest.fail(f"【{case_name}】请求体格式错误：{str(e)}")

        # 5. 发送提交订单请求（修正step名称，不是登录请求！）
        with allure.step("发送提交订单请求"):
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.request(
                    method=method,
                    url=order_url,
                    headers=headers,
                    data=payload,
                    timeout=15
                )
                response_text = response.text
                allure.attach(response_text, f"{case_name} - 响应内容", allure.attachment_type.JSON)
                print(f"【{case_name}】订单接口响应：{response_text}")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"【{case_name}】订单请求发送失败：{str(e)}")

        # 6. 基础断言（可选）
        with allure.step("断言HTTP状态码"):
            assert response.status_code == int(expected_http_code), \
                f"【{case_name}】状态码错误！预期：{expected_http_code}，实际：{response.status_code}"