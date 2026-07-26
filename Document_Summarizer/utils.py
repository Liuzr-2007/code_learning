# -*- coding: utf-8 -*-
# utils.py — 公共工具与基础设置
"""公共工具模块：日志配置、Windows 文件属性、通用工具函数"""
import os
import ctypes
import logging
import datetime
from pathlib import Path

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Windows 文件属性标志常量
FILE_ATTRIBUTE_READONLY = 0x0001  # 只读文件
FILE_ATTRIBUTE_HIDDEN = 0x0002    # 隐藏文件
FILE_ATTRIBUTE_SYSTEM = 0x0004    # 系统文件
FILE_ATTRIBUTE_DIRECTORY = 0x0010 # 目录/文件夹
FILE_ATTRIBUTE_ARCHIVE = 0x0020   # 存档文件

# 绑定 kernel32 API
kernel32 = ctypes.windll.kernel32
kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
kernel32.GetFileAttributesW.restype = ctypes.c_uint32


def clean_path_input(raw: str) -> Path:
    """统一清理用户输入路径：去引号、去空格、展开环境变量"""
    cleaned = raw.strip().strip('"').strip("'")
    expanded = os.path.expandvars(cleaned)
    return Path(expanded)


def display_width(text: str) -> int:
    """计算字符串显示宽度，中文字符算2，英文算1"""
    return sum(2 if ord(c) > 127 else 1 for c in text)


def get_file_attributes(file_path: Path) -> int:
    """获取Windows文件属性标志，失败返回-1"""
    try:
        return kernel32.GetFileAttributesW(str(file_path))
    except OSError:
        return -1


def is_hidden_file(file_path: Path) -> bool:
    """判断是否拥有隐藏属性"""
    attrs = get_file_attributes(file_path)
    if attrs == -1:
        return False
    return bool(attrs & FILE_ATTRIBUTE_HIDDEN)


def is_system_file(file_path: Path) -> bool:
    """判断是否为系统文件"""
    attrs = get_file_attributes(file_path)
    if attrs == -1:
        return False
    return bool(attrs & FILE_ATTRIBUTE_SYSTEM)


def skip_hidden_system(path: Path) -> bool:
    """综合过滤规则：隐藏/系统文件/点开头文件 返回True=跳过扫描"""
    return is_hidden_file(path) or is_system_file(path) or path.name.startswith(".")


def format_size(byte_num: int) -> str:
    """字节自动格式化 GB/MB/KB/B"""
    if byte_num >= 1024 ** 3:
        return f"{byte_num / (1024 ** 3):.2f} GB"
    elif byte_num >= 1024 ** 2:
        return f"{byte_num / (1024 ** 2):.2f} MB"
    elif byte_num >= 1024:
        return f"{byte_num / 1024:.2f} KB"
    else:
        return f"{byte_num} B"


def get_file_time_str(stat_info, time_type: str = "create") -> str:
    """统一提取文件时间"""
    try:
        if time_type == "create":
            ts = stat_info.st_ctime
        else:
            ts = stat_info.st_mtime
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError) as e:
        return f"读取失败: {str(e)}"


def get_unique_path(base_path: Path) -> Path:
    """如果文件已存在，自动编号 (1), (2), ..."""
    if not base_path.exists():
        return base_path
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
