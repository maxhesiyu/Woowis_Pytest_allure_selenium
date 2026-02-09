from pathlib import Path

from common.log import log


# ========== 统一配置：获取项目根目录 + Excel文件夹路径 ==========
def get_project_root():
    """获取项目根目录（Pytest_allure_2）"""
    # 此文件路径：config/path_config.py → 上一级是config → 再上一级是项目根目录
    current_file = Path(__file__).absolute()
    project_root = current_file.parent.parent  # 调整.parent次数匹配目录结构
    return project_root

"""获取Excel文件夹路径（项目根目录/Excel），自动创建文件夹"""
def get_excel_dir():
    """获取Excel文件夹路径（项目根目录/Excel），自动创建文件夹"""
    project_root = get_project_root()
    excel_dir = project_root / "Excel"  # 统一指向根目录下的Excel文件夹

    # 先判断文件夹是否存在，仅在“不存在→创建”时输出日志
    if not excel_dir.exists():
        excel_dir.mkdir(exist_ok=True)
        log.info(f"✅ 统一Excel目录：{excel_dir}（不存在已自动创建）")

    return excel_dir

def get_excel_file_path(file_name: str):
    """拼接Excel文件的完整路径（Excel文件夹 + 文件名）"""
    excel_dir = get_excel_dir()
    excel_file_path = excel_dir / file_name
    return excel_file_path.absolute()  # 返回绝对路径，避免相对路径问题

# 导出常用变量（方便调用）
PROJECT_ROOT = get_project_root()
EXCEL_DIR = get_excel_dir()