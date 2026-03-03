from pathlib import Path

# 项目根目录（全局配置）
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Excel文件路径配置
EXCEL_PATHS = {
    "account": str(PROJECT_ROOT / "Excel/账号密码.xlsx"),
    "promotion": str(PROJECT_ROOT / "Excel/促销赠品获取参数化.xlsx"),
    "login_case": str(PROJECT_ROOT / "Excel/测试登录参数化.xlsx")
}

# Excel读取配置（按场景分类）
EXCEL_READ_CONFIG = {
    "free_gift": {
        "account": {
            "sheet_name": "Sheet2",
            "parse_sku": False,
            "sku_col_index": 0,
            "str_force_cols": ["账号", "密码"],
            "normalize_cols": ["账号", "密码"]
        },
        "promotion": {
            "sheet_name": "促销",
            "parse_sku": True,
            "sku_col_index": 3,
            "str_force_cols": [],
            "normalize_cols": []
        }
    },
    "login": {  # 新增登录配置
        "account": {
            "sheet_name": "Sheet1",
            "parse_sku": False,
            "sku_col_index": 0,
            "str_force_cols": ["账号", "密码"],
            "normalize_cols": ["账号", "密码"]
        },
        "case_info": {
            "sheet_name": "Sheet1",
            "parse_sku": False,
            "sku_col_index": 0,
            "str_force_cols": [],
            "normalize_cols": []
        }
    }
}

# Excel合并配置（按场景分类）
EXCEL_MERGE_CONFIG = {
    "free_gift": {
        "key_column": "序号",
        "merge_how": "inner",
        "preserve_all_fields": True
    },
    "login": {  # 新增登录合并配置
        "key_column": "序号",
        "merge_how": "inner",
        "preserve_all_fields": True
    }
}