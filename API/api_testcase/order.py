import allure
import pytest
import requests
import json
from typing import Dict, Any, Tuple, List
from urllib.parse import urlencode

from API.api_common.api_base import TestLogin
from common.log import log
from config.path_config import get_excel_file_path
from config.read_from_excel import read_test_data_from_excel


class TestOrder:

    @staticmethod
    def get_order_test_data() -> List[Tuple]:
        """读取订单接口测试用例（返回元组格式的用例列表）"""
        try:
            order_cases = read_test_data_from_excel(
                file_path=str(get_excel_file_path("Excel_API/接口提交订单.xlsx")),
                sheet_name="Sheet1",
                parse_sku=False,
                sku_col_index=0
            )
            if not order_cases:
                log.error("❌ 订单Excel无可用用例数据")
                raise RuntimeError("订单Excel无可用用例数据")
            log.info(f"✅ 成功读取{len(order_cases)}条订单接口测试用例")
            return order_cases
        except Exception as e:
            log.error(f"❌ 读取订单Excel失败：{str(e)}")
            raise

    @pytest.mark.parametrize("case", get_order_test_data())
    @allure.title('{case[0]}')  # 动态显示用例名
    def test_submit_order(self, case: Tuple):
        """订单提交测试方法"""
        # 1. 提取用例数据
        case_name = case[0]  # 用例名
        base_url = case[1]  # 请求URL
        method = case[2].upper()  # 请求方法
        params_str = case[3]# 请求参数（JSON字符串）
        expected_http_code = case[4] # 预期HTTP状态码
        expected_msg = case[5]  # 预期提示信息

        try:
            # 2. 处理请求基础参数（Allure分步记录）
            with allure.step("处理订单请求基础参数"):
                # 校验请求方式（仅支持POST/GET）
                if method not in ["POST", "GET"]:
                    error_msg = f"❌ 【{case_name}】请求方式不正确，仅支持POST/GET，当前方式：{method}"
                    log.error(error_msg)
                    raise ValueError(error_msg)

                # 获取登录Token
                token = TestLogin.get_login_token()
                log.info(f"✅ 【{case_name}】成功获取登录Token：{token}")
                allure.attach(f"Token：{token}", "登录Token", allure.attachment_type.TEXT)

                # 拼接完整URL（带公共参数）
                if not base_url:
                    error_msg = f"❌ 【{case_name}】URL为空，无法发起请求"
                    log.error(error_msg)
                    raise ValueError(error_msg)

                url_params = {"token": token, "m": "og010", "channel": "MyO"}
                encoded_params = urlencode(url_params)
                order_url = f"{base_url}&{encoded_params}" if "?" in base_url else f"{base_url}?{encoded_params}"
                log.info(f"📝 【{case_name}】{method}请求完整URL：{order_url}")
                allure.attach(f"URL：{order_url}\nMethod：{method}", "请求基础信息", allure.attachment_type.TEXT)

            # 3. 处理请求参数（解析JSON，Allure记录）
            with allure.step("处理订单请求参数"):
                try:
                    request_data = json.loads(params_str) if params_str.strip() else {}
                except json.JSONDecodeError as e:
                    error_msg = f"❌ 【{case_name}】请求参数JSON解析失败：{str(e)}"
                    log.error(error_msg)
                    raise

                # 构造请求头
                headers = {
                    'authority': 'cdoqa.doterra.cn',
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    'authorization-method': 'og010',
                    'origin': 'https://qa.doterra.cn',
                    'referer': 'https://qa.doterra.cn/',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-platform': '"Windows"',
                    'content-type': 'application/json;charset=UTF-8',
                }
                allure.attach(json.dumps(headers, ensure_ascii=False, indent=4), "请求头", allure.attachment_type.JSON)

                # 区分请求方式处理参数
                payload_str = ""
                get_params = {}
                if method == "POST":
                    payload = {
                        "paramss": request_data.get("paramss", {}),
                        "withCredentials": request_data.get("withCredentials", False)
                    }
                    payload_str = json.dumps(payload, ensure_ascii=False, indent=4)
                    log.info(f"📤 【{case_name}】POST请求体：\n{payload_str}")
                    allure.attach(payload_str, "POST请求体", allure.attachment_type.JSON)
                elif method == "GET":
                    get_params = request_data.get("paramss", {})
                    log.info(f"📤 【{case_name}】GET请求参数：{get_params}")
                    allure.attach(json.dumps(get_params, ensure_ascii=False, indent=4), "GET请求参数",
                                  allure.attachment_type.JSON)

            # 4. 发送订单请求（Allure分步记录）
            response = None
            response_text = ""
            with allure.step("发送订单接口请求"):
                allure.attach(
                    f"URL：{order_url}\nMethod：{method}\nHeaders：{json.dumps(headers, ensure_ascii=False)}",
                    "请求信息",
                    allure.attachment_type.TEXT
                )
                log.info(f"📤 【{case_name}】发起{method}订单请求")

                if method == "POST":
                    response = requests.post(
                        url=order_url,
                        headers=headers,
                        data=payload_str.encode("utf-8"),
                        timeout=15
                    )
                elif method == "GET":
                    response = requests.get(
                        url=order_url,
                        headers=headers,
                        params=get_params,
                        timeout=15
                    )

                response_text = response.text
                log.info(f"📥 【{case_name}】{method}请求响应状态码：{response.status_code}")
                # 响应内容附加到Allure报告
                allure.attach(response_text, "接口响应内容", allure.attachment_type.JSON)
                log.info(f"📥 【{case_name}】{method}请求响应数据：\n{response_text}")

            # 5. 第一层断言：HTTP状态码+JSON格式
            resp_json = None
            with allure.step("断言接口请求基础成功（HTTP状态码+JSON格式）"):
                # 断言HTTP状态码（统一转int）
                expected_http_code_int = int(expected_http_code) if (
                        isinstance(expected_http_code, str) and expected_http_code.isdigit()
                ) else expected_http_code
                assert response.status_code == expected_http_code_int, \
                    f"【{case_name}】HTTP状态码错误！预期：{expected_http_code_int}，实际：{response.status_code}"
                log.info(f"✅ 【{case_name}】HTTP状态码断言通过（{expected_http_code_int}）")

                # 解析响应为JSON（确保格式正确）
                try:
                    resp_json = response.json()
                except json.JSONDecodeError:
                    resp_json = {
                        "raw_response": response.text,
                        "response_status_code": response.status_code
                    }
                    log.error(f"❌ 【{case_name}】响应非JSON格式：{response.text}")

            # 6. 第二层断言：业务逻辑校验（提示信息校验）
            with allure.step("断言订单接口业务逻辑（提示信息）"):
                # 精准提取业务响应字段
                actual_data_value = resp_json.get("data", {}).get("value", {})
                allure.attach(json.dumps(actual_data_value, ensure_ascii=False, indent=4), "实际返回的data.value",
                              allure.attachment_type.JSON)

                # 断言提示信息（空则不校验，有值才模糊匹配）
                if expected_msg and str(expected_msg).strip() != "":
                    expected_msg_str = str(expected_msg).strip()
                    actual_msg_str = actual_data_value.get("message", "").strip()
                    # 清理特殊标签，避免匹配失败
                    actual_msg_clean = actual_msg_str.replace("<br>", "").replace("\n", "")
                    assert expected_msg_str in actual_msg_clean, \
                        f"【{case_name}】提示信息断言错误！\n" \
                        f"预期包含：{expected_msg_str}\n实际（已清理）：{actual_msg_clean}"
                    log.info(f"✅ 【{case_name}】提示信息断言通过（包含：{expected_msg_str}）")
                else:
                    allure.attach(f"用例【{case_name}】expected_msg为空，跳过提示信息校验", "提示")
                    log.info(f"ℹ️ 【{case_name}】expected_msg为空，跳过提示信息校验")

            # 仅当所有逻辑执行完成（无异常），才输出通过提示
            log.info(f"🎉 【{case_name}】订单接口测试通过！")

        except json.JSONDecodeError as e:
            # 捕获JSON解析错误
            error_msg = f"❌ 【{case_name}】JSON解析失败：{str(e)}"
            log.error(error_msg)
            allure.attach(error_msg, "错误信息", allure.attachment_type.TEXT)
            pytest.fail(error_msg)  # 标记用例失败，不终止其他用例
        except requests.exceptions.RequestException as e:
            # 捕获请求异常（超时/连接错误等）
            error_msg = f"❌ 【{case_name}】接口请求失败：{str(e)}（URL：{order_url if 'order_url' in locals() else base_url}）"
            log.error(error_msg)
            allure.attach(error_msg, "错误信息", allure.attachment_type.TEXT)
            pytest.fail(error_msg)
        except AssertionError as e:
            # 捕获断言失败（核心：打印失败提示后重新抛出，保证pytest记录失败）
            error_msg = f"❌ 【{case_name}】订单接口测试失败：{str(e)}"
            log.error(error_msg)
            allure.attach(error_msg, "断言失败信息", allure.attachment_type.TEXT)
            raise  # 重新抛出断言异常，让pytest标记用例失败
        except ValueError as e:
            # 捕获请求方式/URL为空等业务异常
            error_msg = f"❌ 【{case_name}】订单接口参数错误：{str(e)}"
            log.error(error_msg)
            allure.attach(error_msg, "参数错误信息", allure.attachment_type.TEXT)
            pytest.fail(error_msg)
        except Exception as e:
            # 捕获其他未知异常
            error_msg = f"❌ 【{case_name}】订单接口测试异常：{str(e)}"
            log.error(error_msg)
            allure.attach(error_msg, "未知异常信息", allure.attachment_type.TEXT)
            pytest.fail(error_msg)


if __name__ == "__main__":
    """调试运行"""
    order_test = TestOrder()
    cases = order_test.get_order_test_data()
    for case in cases:
        order_test.test_submit_order(case)