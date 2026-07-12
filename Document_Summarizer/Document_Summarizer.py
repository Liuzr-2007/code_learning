# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
import datetime

def get_file_creat_time(file_path:Path):
    #获取文件创建时间
    try:
        timestamp = file_path.stat().st_ctime
        creat_time = datetime.datetime.fromtimestamp(timestamp)
        return creat_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Error: {e}"

def get_file_mod_time(file_path:Path):
    #获取文件修改时间
    try:
        timestamp = file_path.stat().st_mtime
        mod_time = datetime.datetime.fromtimestamp(timestamp)
        return mod_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Error: {e}"

#遍历目标文件夹，统计文件数量、总大小、子文件夹数、
#各类型文件分布、目录树摘要，返回结构化字典信息
def collect_folder_info(folder_path):
    target = Path(folder_path)
    #可选扩展方向
    # 过滤隐藏文件 / 系统文件(避免显示不必要的文件，尚未解决)
    # 限制递归深度，避免超大目录卡死
    # 单独统计最大 / 最小文件
    # 需要我给你加限制遍历深度或筛选指定后缀的版本吗？
    if not target.is_dir():
        print("Error: NOT EFFECTIVE FOLDER_PATH!")
        return
    #提示进度
    print(f"==========正在收集信息:{target}==========")
    all_files = []

    #递归遍历 target 目录每一层，
    #root 当前目录路径，files 当前目录下所有文件名列表。
    for root, dirs, files in os.walk(target):
        #循环当前层每一个文件名称。
        for filename in files:
            #用 pathlib 拼接得到文件完整路径对象
            file_full = Path(root)/filename
            try:
                file_size = file_full.stat().st_size
            except PermissionError:
                file_size = "无访问权限"
            except FileExistsError:
                file_size = "文件不存在"
            except Exception as e:
                file_size = f"其他错误: {e}"
            file_info = {
                "name": filename,
                "path": str(file_full),
                #获取文件占用字节大小；无权限访问时会抛异常，
                #建议加 try-except。
                "size": file_full.stat().st_size,
                "create_time": get_file_creat_time(file_full),
                "mod_time": get_file_mod_time(file_full)
            }
            #file_info 字典存储单文件信息，
            #追加到 all_files 列表统一收集
            all_files.append(file_info)
            print(f"name: {file_info['name']}")
            print(f"path: {file_info['path']}")
            print(f"size: {file_info['size']} bytes")
            print(f"create_time: {file_info['create_time']}")
            print(f"mod_time: {file_info['mod_time']}")
            print("----------------------------------------")

    with open("文件夹信息汇总.txt", "w", encoding="utf-8") as f:
        for info in all_files:
            f.write(f"{info}\n")
    print(f"\n收集完成，共扫描{len(all_files)}个文件，信息已保存到 文件夹信息汇总.txt")

if __name__ == "__main__":
    # 调试专用：写死目标文件夹路径
    folder_input = r"D:\c++\work\Document Summarizer\test"
    collect_folder_info(folder_input)
    if len(sys.argv) < 2:
        print("使用方法：将文件夹拖拽到本程序/终端窗口内运行")
        input("按回车退出...")
    else:
        # 第一个参数是程序本身，后面是拖拽进来的路径
        folder_input = sys.argv[1]
        collect_folder_info(folder_input)
        input("\n扫描完毕，按回车关闭窗口")