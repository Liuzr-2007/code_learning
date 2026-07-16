# -*- coding: utf-8 -*-
import os
import sys
import ctypes
import datetime
from pathlib import Path
from collections import defaultdict

# Windows 文件属性标志常量
FILE_ATTRIBUTE_READONLY   = 0x0001  # 只读文件
FILE_ATTRIBUTE_HIDDEN     = 0x0002  # 隐藏文件
FILE_ATTRIBUTE_SYSTEM     = 0x0004  # 系统文件
FILE_ATTRIBUTE_DIRECTORY  = 0x0010  # 目录/文件夹
FILE_ATTRIBUTE_ARCHIVE    = 0x0020  # 存档文件

# 绑定 kernel32 API，严格指定参数、返回值类型，规避类型转换报错
kernel32 = ctypes.windll.kernel32
kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
kernel32.GetFileAttributesW.restype = ctypes.c_uint32

def get_file_attributes(file_path: Path) -> int:
    """获取Windows文件属性标志，失败返回-1"""
    try:
        return kernel32.GetFileAttributesW(str(file_path))
    except Exception:
        return -1

def is_hidden_file(file_path: Path) -> bool:
    """判断是否拥有隐藏属性：存在且隐藏返回True"""
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
    """字节自动格式化 GB/MB/KB/B，提升报告可读性"""
    if byte_num >= 1024 ** 3:
        return f"{byte_num / (1024 ** 3):.2f} GB"
    elif byte_num >= 1024 ** 2:
        return f"{byte_num / (1024 ** 2):.2f} MB"
    elif byte_num >= 1024:
        return f"{byte_num / 1024:.2f} KB"
    else:
        return f"{byte_num} B"

# 修复：补充函数末尾缺失冒号
def get_file_time_str(stat_info, time_type: str = "create") -> str:
    """
    统一提取文件时间，仅调用一次stat后复用
    :param stat_info: Path.stat() 对象
    :param time_type: create=创建时间(Windows专用) modify=修改时间
    """
    try:
        if time_type == "create":
            # Windows下 st_ctime = 文件创建时间；Linux下为inode变更时间，无真实创建时间
            ts = stat_info.st_ctime
        else:
            ts = stat_info.st_mtime
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"读取失败: {str(e)}"

def collect_folder_info(folder_input: str):
    """
    遍历目标文件夹，统计文件数量、总大小、子文件夹数、后缀分布，输出明细+汇总文本报告
    :param folder_input: 原始输入路径（拖拽/手动输入）
    """
    # 修复：消除转义警告，分开剥离引号
    clean_path = folder_input.strip().strip('"').strip("'")
    target = Path(clean_path)

    if not target.is_dir():
        print(f"错误：路径「{target}」不是有效文件夹！")
        return

    # 选择是否扫描隐藏/系统文件
    while True:
        choose_hidden = input("是否一并查询隐藏/系统文件？输入 y 包含，n 过滤：").strip().lower()
        if choose_hidden in ("y", "n"):
            break
        print("无效输入，请输入 y 或 n")

    print(f"\n==========开始扫描目录: {target} ==========")
    all_files = []
    suffix_counter = defaultdict(int)
    total_byte = 0
    dir_count = 0  # 新增：统计子文件夹总数
    read_fail_count = 0  # 读取失败文件计数

    # os.walk 自上而下遍历目录树
    for root, dirs, files in os.walk(target):
        current_root = Path(root)
        print(f"正在扫描目录: {current_root}")

        # 过滤不需要遍历的子目录（原地修改dirs，os.walk不再递归进入）
        if choose_hidden == "n":
            dirs[:] = [d for d in dirs if not skip_hidden_system(current_root / d)]
        dir_count += len(dirs)

        # 遍历当前目录所有文件
        for filename in files:
            file_full = current_root / filename
            # 过滤隐藏/系统/点文件
            if choose_hidden == "n" and skip_hidden_system(file_full):
                continue

            # 仅单次stat获取全部元数据，减少磁盘IO
            try:
                stat_info = file_full.stat()
                file_size = stat_info.st_size
                total_byte += file_size
                err_msg = None
            except PermissionError:
                file_size = 0
                err_msg = "权限不足，无法读取大小"
                read_fail_count += 1
            except FileNotFoundError:
                file_size = 0
                err_msg = "文件已被删除"
                read_fail_count += 1
            except OSError as e:
                file_size = 0
                err_msg = f"IO异常: {str(e)}"
                read_fail_count += 1

            # 获取格式化时间
            create_t = get_file_time_str(stat_info, "create") if err_msg is None else err_msg
            mod_t = get_file_time_str(stat_info, "modify") if err_msg is None else err_msg
            suffix = file_full.suffix if file_full.suffix else "无后缀"
            suffix_counter[suffix] += 1

            file_info = {
                "name": filename,
                "path": str(file_full),
                "size_byte": file_size,
                "size_str": format_size(file_size) if err_msg is None else err_msg,
                "create_time": create_t,
                "modify_time": mod_t
            }
            all_files.append(file_info)

            # 控制台实时打印单文件信息
            print(f"【文件】{file_info['name']} | {file_info['size_str']}")
            print(f"完整路径: {file_info['path']}")
            print(f"创建: {create_t} | 修改: {mod_t}")
            print("-" * 60)

    # 生成带时间戳的报告文件名，避免覆盖旧报告
    time_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"文件夹扫描报告_{time_suffix}.txt"

    # 写入汇总报告
    with open(report_name, "w", encoding="utf-8") as f:
        scan_mode = "（包含隐藏/系统文件）" if choose_hidden == "y" else "（已过滤隐藏/系统文件）"
        f.write(f"===== 文件夹扫描汇总报告 {scan_mode} =====\n")
        f.write(f"扫描根目录：{target}\n")
        f.write(f"扫描时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"子文件夹总数：{dir_count} 个\n")
        f.write(f"有效文件总数：{len(all_files)} 个\n")
        f.write(f"读取失败文件：{read_fail_count} 个\n")
        f.write(f"总占用空间：{format_size(total_byte)}\n\n")

        f.write("===== 文件后缀分类统计 =====\n")
        # 按文件数量倒序输出后缀
        sorted_suffix = sorted(suffix_counter.items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_suffix:
            f.write(f"{ext:10s}：{count:4d} 个\n")

        f.write("\n===== 全部文件明细列表 =====\n")
        for info in all_files:
            f.write("-" * 60 + "\n")
            f.write(f"文件名：{info['name']}\n")
            f.write(f"完整路径：{info['path']}\n")
            f.write(f"文件大小：{info['size_str']}\n")
            f.write(f"创建时间：{info['create_time']}\n")
            f.write(f"修改时间：{info['modify_time']}\n")

    # 扫描完成控制台汇总输出
    print(f"\n==================== 扫描完成 ====================")
    print(f"根目录子文件夹：{dir_count} 个")
    print(f"扫描到文件总数：{len(all_files)} 个")
    print(f"读取失败文件：{read_fail_count} 个")
    print(f"目录总占用空间：{format_size(total_byte)}")
    print(f"完整报告已保存至：{os.path.abspath(report_name)}")

if __name__ == "__main__":
    print("\n==================== 文件扫描工具主菜单 ====================")
    print("[CFI] 执行文件夹深度扫描统计（当前功能）")
    print("[q]   退出程序")
    print("其他输入：预留扩展功能2")
    print("===========================================================\n")

    # 严格统一4空格缩进，解决IndentationError
    while True:
        choice = input("请输入功能指令：").strip()

        if choice.lower() == "q":
            print("程序正常退出")
            sys.exit(0)
        elif choice.upper() == "CFI":
            # 处理拖拽启动参数
            if len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入目标文件夹路径（可直接拖拽文件夹到窗口）：")
            collect_folder_info(folder_input)
            input("\n按回车键返回功能菜单...")
        else:
            print("功能2待开发，仅占位预留")
            input("按回车键返回菜单")