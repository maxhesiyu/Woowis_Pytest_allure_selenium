import allure
import pytest
import requests
import json

from config.path_config import get_excel_file_path
from config.read_from_excel import read_test_data_from_excel


class TestLogin:
    """登录接口测试类"""

    @pytest.mark.parametrize(
        "case",
        read_test_data_from_excel(
            file_path=str(get_excel_file_path("接口登录参数化.xlsx")),
            sheet_name="Sheet1",
            parse_sku=False,
            sku_col_index=0
        )
    )
    @allure.title('{case[0]}')  # 动态显示用例名（优先用表格中的用例名）
    def test_api_login(self, case):
        # 1. 提取用例数据（明确列含义）
        case_name = case[0]  # 用例名
        url = case[1]  # 请求URL
        method = case[2].upper()  # 请求方法（统一转大写）
        body_str = case[3]  # 请求体（字符串JSON）
        expected_http_code = case[4]  # 预期HTTP状态码（如200）
        expected_value_json = case[5]  # 表格中需校验的返回体（可能为None/空）

        # 2. 解析表格中的“预期对象”（兼容None/空值）
        expected_Value = None
        expected_VipNo = None
        with allure.step("处理表格预期返回体数据"):
            try:
                # 关键修复：先判断预期值是否为None/空字符串，跳过无效解析
                if expected_value_json is None or str(expected_value_json).strip() == "":
                    with allure.step(f"用例【{case_name}】表格中需校验的返回体为空，跳过预期值解析"):
                         allure.attach(f"用例【{case_name}】表格中需校验的返回体为空，跳过预期值解析", "提示")
                         print(f"【{case_name}】表格中需校验的返回体为空，跳过预期值解析")
                else:
                    # 修复表格预期值格式（兼容不完整JSON）
                    expected_value_clean = str(expected_value_json).strip().strip('"')
                    if not expected_value_clean.startswith('{'):
                        expected_value_clean = '{' + expected_value_clean
                    if not expected_value_clean.endswith('}'):
                        expected_value_clean += '}'

                    # 解析为字典并提取预期值
                    expected_value_dict = json.loads(expected_value_clean)
                    expected_Value = expected_value_dict["value"]["Value"]  # 预期：1（int）
                    expected_VipNo = expected_value_dict["value"]["VipNo"]  # 预期：（str）
                    allure.attach(
                        f"预期Value：{expected_Value}, 预期VipNo：{expected_VipNo}",
                        "表格预期值"
                    )
                    print(f"【{case_name}】表格预期value：Value={expected_Value}, VipNo={expected_VipNo}")
            except (json.JSONDecodeError, KeyError) as e:
                pytest.fail(f"【{case_name}】表格中预期返回体格式错误：{expected_value_json}，错误：{str(e)}")

        # 3. 处理请求体（避免双重序列化）
        with allure.step("处理登录请求体"):
            try:
                body_dict = json.loads(body_str)
                payload = json.dumps(body_dict, ensure_ascii=False)
                allure.attach(payload, "格式化后请求体", allure.attachment_type.JSON)
                print(f"【{case_name}】请求体：{payload}")
            except json.JSONDecodeError as e:
                pytest.fail(f"【{case_name}】请求体格式错误：{body_str}，错误：{str(e)}")

        # 4. 发送登录请求
        response = None
        response_text = ""
        with allure.step("发送登录接口请求"):
            headers = {'Content-Type': 'application/json'}
            allure.attach(
                f"URL：{url}\nMethod：{method}\nHeaders：{headers}",
                "请求信息"
            )
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=payload,
                    timeout=15
                )
                response_text = response.text
                # 响应内容附加到Allure报告
                allure.attach(response_text, "接口响应内容", allure.attachment_type.JSON)
                print(f"【{case_name}】接口响应：{response_text}")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"【{case_name}】请求失败：{str(e)}（URL：{url}）")

        # 5. 第一层断言：请求基础成功（HTTP状态码+JSON格式）
        resp_json = None
        with allure.step("断言接口请求基础成功（HTTP状态码+JSON格式）"):
            # 断言HTTP状态码
            assert response.status_code == int(expected_http_code), \
                f"【{case_name}】HTTP状态码错误！预期：{expected_http_code}，实际：{response.status_code}"

            # 解析响应为JSON（确保格式正确）
            try:
                resp_json = response.json()
            except json.JSONDecodeError:
                pytest.fail(f"【{case_name}】响应非JSON格式：{response_text}")

        # 6. 第二层断言：精准校验嵌套的value对象（兼容空预期值）
        with allure.step("断言返回体中data.value字段值"):
            # 精准提取接口返回的data.value对象（用get兜底，避免字段不存在报错）
            actual_data_value = resp_json.get("data", {}).get("value", {})
            allure.attach(str(actual_data_value), "实际返回的data.value", allure.attachment_type.TEXT)

            # 仅当预期值非空时，才执行Value和VipNo的断言
            if expected_Value is not None and expected_VipNo is not None:
                # 断言1：data.value.Value 等于 预期Value（注意类型匹配：int）
                actual_Value = actual_data_value.get("Value")
                # 处理表格预期值类型（可能是字符串“1”，需转int）
                expected_Value = int(expected_Value) if (
                        isinstance(expected_Value, str) and expected_Value.isdigit()
                ) else expected_Value

                assert actual_Value == expected_Value, \
                    f"【{case_name}】data.value.Value断言错误！\n" \
                    f"预期：{expected_Value}（类型：{type(expected_Value)}）\n" \
                    f"实际：{actual_Value}（类型：{type(actual_Value)}）"

                # 断言2：data.value.VipNo 等于 预期VipNo（字符串精确匹配）
                actual_VipNo = actual_data_value.get("VipNo")
                assert actual_VipNo == expected_VipNo, \
                    f"【{case_name}】data.value.VipNo断言错误！\n" \
                    f"预期：{expected_VipNo}\n实际：{actual_VipNo}"
            else:
                allure.attach(f"用例【{case_name}】无预期断言，跳过校验", "提示")
                print(f"【{case_name}】无预期断言，跳过校验")

        # 7. 用例通过提示
        print(f"🎉 【{case_name}】登录接口测试通过！")