import pandas as pd
import ast
from pathlib import Path
from typing import List, Dict, Union
from common.log import log

class ExcelHandler:
    """Excel读取、解析、合并工具类"""

    @staticmethod
    def normalize_columns(df: pd.DataFrame, normalize_cols: List[str]) -> pd.DataFrame:
        """
        通用列标准化处理函数
        :param df: 待处理的DataFrame
        :param normalize_cols: 需要标准化的列名列表（空列表则跳过处理）
        :return: 标准化后的DataFrame
        """
        if not isinstance(normalize_cols, List):
            raise TypeError("normalize_cols必须是列表类型")

        if len(normalize_cols) == 0:
            log.info("标准化列名列表为空，跳过列标准化处理")
            return df

        for col in normalize_cols:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: "" if pd.isna(x) else str(x).strip()
                )
                log.info(f"已标准化列：{col}，空值已转为空字符串，值已去除首尾空格")
            else:
                log.warning(f"待标准化列「{col}」不存在于表格中，跳过处理")

        return df

    @staticmethod
    def read_excel(
            file_path: Union[str, Path],
            sheet_name: str,
            parse_sku: bool,
            sku_col_index: int,
            str_force_cols: List[str],
            normalize_cols: List[str]
    ) -> pd.DataFrame:
        """
        读取Excel文件并解析SKU列
        """
        # 参数类型校验
        if not isinstance(file_path, (str, Path)):
            raise TypeError("file_path必须是字符串或Path类型")
        if not isinstance(sheet_name, str):
            raise TypeError("sheet_name必须是字符串类型")
        if not isinstance(parse_sku, bool):
            raise TypeError("parse_sku必须是布尔类型")
        if not isinstance(sku_col_index, int) or sku_col_index < 0:
            raise ValueError("sku_col_index必须是非负整数")
        if not isinstance(str_force_cols, List):
            raise TypeError("str_force_cols必须是列表类型")
        if not isinstance(normalize_cols, List):
            raise TypeError("normalize_cols必须是列表类型")

        # 验证文件存在性
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")

        # 构建dtype字典
        dtype_config = {}
        if len(str_force_cols) > 0:
            header_df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
            cols = header_df.columns.tolist()
            for col in str_force_cols:
                if col in cols:
                    dtype_config[col] = str
                    log.info(f"已配置列「{col}」强制转为字符串类型")
                else:
                    log.warning(f"强制字符串列「{col}」不存在于表格中，跳过配置")

        # 读取Excel
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=dtype_config)
            log.info(f"成功读取Excel：{file_path.name} - {sheet_name}，行数：{len(df)}，列数：{len(df.columns)}")
        except Exception as e:
            raise RuntimeError(f"读取Excel失败：{str(e)}") from e

        # 列标准化
        df = ExcelHandler.normalize_columns(df, normalize_cols)

        # 解析SKU列
        if parse_sku:
            if len(df.columns) <= sku_col_index:
                raise IndexError(f"SKU列索引{sku_col_index}超出表格列范围（总列数：{len(df.columns)}）")

            sku_col = df.columns[sku_col_index]
            parsed_skus = []
            for sku_raw in df[sku_col]:
                if pd.isna(sku_raw):
                    parsed_skus.append([])
                    continue
                if isinstance(sku_raw, str):
                    if sku_raw.startswith("[") and sku_raw.endswith("]"):
                        try:
                            sku_list = ast.literal_eval(sku_raw)
                        except:
                            sku_list = [sku_raw]
                    elif "," in sku_raw:
                        sku_list = [s.strip() for s in sku_raw.split(",")]
                    else:
                        sku_list = [sku_raw]
                else:
                    sku_list = [sku_raw]
                parsed_skus.append(sku_list)
            df[sku_col] = parsed_skus
            log.info(f"已解析SKU列：{sku_col}，共解析{len(parsed_skus)}行数据")

        return df

    @staticmethod
    def merge_excel(
            excel_config_list: List[Dict],
            key_column: str,
            merge_how: str = "inner",
            preserve_all_fields: bool = True
    ) -> pd.DataFrame:
        """
        合并多个Excel表格
        :param excel_config_list: 配置列表，每个元素包含：path, sheet_name, parse_sku, sku_col_index, str_force_cols, normalize_cols
        :param key_column: 关联关键字段
        :param merge_how: 合并方式（inner/outer/left/right）
        :param preserve_all_fields: 是否保留所有字段
        :return: 合并后的DataFrame
        """
        # 参数校验
        if not isinstance(excel_config_list, List) or len(excel_config_list) < 2:
            raise ValueError("excel_config_list必须是包含至少2个元素的列表")
        if not isinstance(key_column, str):
            raise TypeError("key_column必须是字符串类型")
        if merge_how not in ["inner", "outer", "left", "right"]:
            raise ValueError("how必须是inner/outer/left/right中的一种")
        if not isinstance(preserve_all_fields, bool):
            raise TypeError("preserve_all_fields必须是布尔类型")

        # 读取第一个Excel作为初始数据
        first_config = excel_config_list[0]
        merged_df = ExcelHandler.read_excel(**first_config)

        # 检查关键字段
        if key_column not in merged_df.columns:
            raise ValueError(f"关键字段 '{key_column}' 在第一个表格中不存在")

        # 依次合并后续表格
        for excel_config in excel_config_list[1:]:
            curr_df = ExcelHandler.read_excel(**excel_config)
            curr_file_name = Path(excel_config["file_path"]).name

            if key_column not in curr_df.columns:
                raise ValueError(f"关键字段 '{key_column}' 在表格 {curr_file_name} 中不存在")

            # 执行合并
            if preserve_all_fields:
                temp_merge = pd.merge(merged_df, curr_df, on=key_column, how=merge_how)
            else:
                common_cols = list(set(merged_df.columns) & set(curr_df.columns))
                if key_column not in common_cols:
                    common_cols.append(key_column)
                temp_merge = pd.merge(
                    merged_df[common_cols],
                    curr_df[common_cols],
                    on=key_column,
                    how=merge_how
                )

            log.info(f"与{curr_file_name} {merge_how}合并后，行数：{len(temp_merge)}，列数：{len(temp_merge.columns)}")
            merged_df = temp_merge

        merged_df = merged_df.reset_index(drop=True)
        log.info(f"合并完成！最终结果：行数{len(merged_df)}，列数{len(merged_df.columns)}")
        return merged_df

    @staticmethod
    def print_data_detail(df: pd.DataFrame):
        """超详细打印合并后的数据"""
        if df.empty:
            log.warning("合并后的数据为空")
            print("⚠️ 合并后的数据为空！")
            return

        print("\n" + "=" * 100)
        print("📊 合并后数据 - 完整表格展示")
        print("=" * 100)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_colwidth', 100)
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        pd.set_option('display.unicode.east_asian_width', True)
        print(df)

        print("\n" + "-" * 100)
        print("📋 合并后数据 - 原始列表格式（字典列表）")
        print("-" * 100)
        raw_data = df.to_dict('records')
        for idx, row in enumerate(raw_data):
            print(f"第{idx + 1}行：{row}")

        print("\n" + "-" * 100)
        print("🔍 数据类型信息")
        print("-" * 100)
        print(df.dtypes)

        print("\n" + "-" * 100)
        print("📝 空值统计")
        print("-" * 100)
        null_stats = df.isnull().sum()
        for col, null_count in null_stats.items():
            print(f"列「{col}」：空值数量 = {null_count}（占比 {null_count / len(df) * 100:.2f}%）")

        print("\n" + "=" * 100)
        print("📈 合并数据摘要")
        print("=" * 100)
        print(f"✅ 总行数：{len(df)}")
        print(f"✅ 总列数：{len(df.columns)}")
        print(f"✅ 列名列表：{df.columns.tolist()}")
        print("=" * 100 + "\n")