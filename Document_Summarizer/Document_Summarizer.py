# -*- coding: utf-8 -*-
import os
import sys
import ctypes
import datetime
from pathlib import Path
from collections import defaultdict


# Windows 文件属性标志常量
FILE_ATTRIBUTE_READONLY   = 0x0001  # 1  只读文件
FILE_ATTRIBUTE_HIDDEN     = 0x0002  # 2  隐藏文件
FILE_ATTRIBUTE_SYSTEM     = 0x0004  # 4  系统文件
FILE_ATTRIBUTE_DIRECTORY  = 0x0010  # 16 目录/文件夹
FILE_ATTRIBUTE_ARCHIVE    = 0x0020  # 32 存档文件

# 绑定 kernel32 API，指定参数、返回值类型，规避类型错误
kernel32 = ctypes.windll.kernel32
kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
kernel32.GetFileAttributesW.restype = ctypes.c_uint32

def get_file_attributes(file_path:Path)->int:
    """获取文件属性标志"""
    try:
        return kernel32.GetFileAttributesW(str(file_path))
    except Exception:
        return -1

def is_hidden_file(file_path:Path)->bool:
        
    """判断文件/文件夹是否拥有隐藏属性
    :param file_path: 文件/目录路径 Path 对象
    :return: 存在且隐藏返回 True，不存在/无隐藏属性返回 False
    """
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

def skip_hidden_system(path:Path)->bool:
    """综合过滤：隐藏文件/系统文件/.开头文件 返回True=跳过不扫描"""
    if is_hidden_file(path) or is_system_file(path):
        return True
    if path.name.startswith("."):
        return True
    return False

def get_file_create_time(file_path:Path):
    """获取文件创建时间"""
    try:
        timestamp = file_path.stat().st_ctime
        create_time = datetime.datetime.fromtimestamp(timestamp)
        return create_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Error: {e}"

def get_file_mod_time(file_path:Path):
    """获取文件修改时间"""
    try:
        timestamp = file_path.stat().st_mtime
        mod_time = datetime.datetime.fromtimestamp(timestamp)
        return mod_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Error: {e}"

def collect_folder_info(folder_path):
    """
    遍历目标文件夹，统计文件数量、总大小、子文件夹数、
    各类型文件分布、目录树摘要，返回结构化字典信息
    :param folder_path: 目标文件夹路径
    """
    target = Path(folder_path)

    if not target.is_dir():
        print("Error: NOT EFFECTIVE FOLDER_PATH!")
        return

    # 新增：询问是否查询隐藏文件
    while True:
        choose_hidden = input("是否一并查询隐藏/系统文件？输入 y 包含，n 过滤：").strip().lower()
        if choose_hidden in ['y', 'n']:
            break
        print("无效输入，请输入 y 或 n")

    #提示进度
    print(f"==========正在收集信息:{target}==========")
    all_files = []
    suffix_counter = defaultdict(int)  # 用于统计各类型文件数量
    total_byte = 0

    #递归遍历 target 目录每一层，
    #root 当前目录路径，files 当前目录下所有文件名列表。
    for root, dirs, files in os.walk(target):
        if choose_hidden == 'n':
            dirs[:] = [d for d in dirs if not skip_hidden_system(Path(root)/d)]

        #循环当前层每一个文件名称。
        for filename in files:
            #用 pathlib 拼接得到文件完整路径对象
            file_full = Path(root)/filename

            if choose_hidden == 'n' and skip_hidden_system(file_full):
                continue

            # 仅调用一次stat，统一获取大小、时间，避免重复IO
            try:
                stat_info = file_full.stat()
                file_size = stat_info.st_size
                total_byte += file_size
            except PermissionError:
                file_size = "无访问权限"
            except FileExistsError:
                file_size = "文件不存在"
            except Exception as e:
                file_size = f"其他错误: {e}"

            create_t = get_file_create_time(file_full)
            mod_t = get_file_mod_time(file_full)
            suffix = file_full.suffix if file_full.suffix else "无后缀"
            suffix_counter[suffix] += 1

            file_info = {
                "name": filename,
                "path": str(file_full),
                "size_byte": file_size,
                "create_time": create_t,
                "modify_time": mod_t
            }
            #file_info 字典存储单文件信息，
            #追加到 all_files 列表统一收集
            all_files.append(file_info)
            print(f"文件名: {file_info['name']}")
            print(f"路径: {file_info['path']}")
            print(f"大小: {file_info['size_byte']} bytes")
            print(f"创建时间: {file_info['create_time']}")
            print(f"修改时间: {file_info['modify_time']}")
            print("-" * 48)

    with open("文件夹信息汇总.txt", "w", encoding="utf-8") as f:
        if choose_hidden == 'y':
            f.write("===== 文件夹扫描汇总报告（包含隐藏/系统文件）=====\n")
        else:
            f.write("===== 文件夹扫描汇总报告（已过滤隐藏/系统文件）=====\n")
        f.write(f"扫描目录：{target}\n")
        f.write(f"有效文件总数：{len(all_files)} 个\n")
        if isinstance(total_byte, int):
            f.write(f"总占用空间：{total_byte / 1024 / 1024:.2f} MB\n\n")
        else:
            f.write("总占用空间：存在读取失败文件，无法完整统计\n\n")

        f.write("===== 文件后缀分类统计 =====\n")
        for ext, count in suffix_counter.items():
            f.write(f"{ext}：{count} 个\n")
        
        f.write("\n===== 全部文件明细列表 =====\n")
        for info in all_files:
            f.write("----------------------------------------\n")
            f.write(f"文件名：{info['name']}\n")
            f.write(f"完整路径：{info['path']}\n")
            f.write(f"文件大小：{info['size_byte']} 字节\n")
            f.write(f"创建时间：{info['create_time']}\n")
            f.write(f"修改时间：{info['modify_time']}\n")
    print(f"\n收集完成，共扫描{len(all_files)}个有效文件\n")
    if isinstance(total_byte, int):
        print(f"文件夹总容量：{total_byte / 1024 / 1024:.2f} MB")
    print("完整报告已保存至：文件夹信息汇总.txt")

#help(collect_folder_info)查看函数功能

if __name__ == "__main__":
    

    print("\n==================== 功能选择菜单 ====================")
    print("输入 CFI ：执行文件夹扫描统计（原程序功能）")
    print("输入其他任意字符：执行功能2")
    print("输入 q ：退出程序")
    while True:
        choice = input("请输入你的选择：").strip()


        if choice.lower() == "q":
            print("程序已退出。")
            sys.exit(0)
        elif choice.upper() == "CFI":
            # 调试专用：写死目标文件夹路径
            # folder_input = r"D:\c++\work\Document Summarizer\test"
            if len(sys.argv) < 2:
                print("使用方法：将文件夹拖拽到本程序/终端窗口内运行")
                folder_input = input("目标文件夹路径：").strip(' "')
            else:
                # 第一个参数是程序本身，后面是拖拽进来的路径
                folder_input = sys.argv[1]
            collect_folder_info(folder_input)
            input("\n扫描完成，按回车键返回功能菜单...")
        else:
            # 预留功能2
            print("功能2待开发")
            input("按回车返回菜单")
                