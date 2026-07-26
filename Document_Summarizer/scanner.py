# -*- coding: utf-8 -*-
"""文件夹扫描模块（CFI 功能）：遍历目录生成扫描统计 txt 报告"""
import os
import datetime
from collections import defaultdict
from pathlib import Path

from utils import (
    clean_path_input,
    format_size,
    get_file_time_str,
    get_unique_path,
    skip_hidden_system,
    logger,
)


def collect_folder_info(folder_input: str) -> None:
    """遍历文件夹生成扫描统计txt报告"""
    target = clean_path_input(folder_input)

    if not target.is_dir():
        logger.error(f"路径「{target}」不是有效文件夹！")
        return

    while True:
        choose_hidden = input("是否一并查询隐藏/系统文件？输入 y 包含，n 过滤：").strip().lower()
        if choose_hidden in ("y", "n"):
            break
        print("无效输入，请输入 y 或 n")

    # 记录统一扫描时间（修复双重 datetime.now() 问题）
    scan_time = datetime.datetime.now()
    time_suffix = scan_time.strftime("%Y%m%d_%H%M%S")

    print(f"\n==========开始扫描目录: {target} ==========")
    all_files: list[dict] = []
    suffix_counter: dict[str, int] = defaultdict(int)
    total_byte = 0
    dir_count = 0
    read_fail_count = 0

    for root, dirs, files in os.walk(target):
        current_root = Path(root)
        print(f"正在扫描目录: {current_root}")

        if choose_hidden == "n":
            dirs[:] = [d for d in dirs if not skip_hidden_system(current_root / d)]
        dir_count += len(dirs)

        for filename in files:
            file_full = current_root / filename
            if choose_hidden == "n" and skip_hidden_system(file_full):
                continue

            # 修复：初始化 stat_info 防止未定义崩溃
            stat_info = None
            try:
                stat_info = file_full.stat()
                file_size = stat_info.st_size
                total_byte += file_size
                err_msg = None
            except (PermissionError, FileNotFoundError, OSError) as e:
                file_size = 0
                err_msg = str(e)
                read_fail_count += 1

            # 修复：用 stat_info is not None 判断，而非 err_msg
            create_t = get_file_time_str(stat_info, "create") if stat_info is not None else err_msg
            mod_t = get_file_time_str(stat_info, "modify") if stat_info is not None else err_msg
            suffix = file_full.suffix if file_full.suffix else "无后缀"
            suffix_counter[suffix] += 1

            file_info = {
                "name": filename,
                "path": str(file_full),
                "size_byte": file_size,
                "size_str": format_size(file_size) if stat_info is not None else err_msg,
                "create_time": create_t,
                "modify_time": mod_t
            }
            all_files.append(file_info)
            print(f"【文件】{file_info['name']} | {file_info['size_str']}")
            print(f"完整路径: {file_info['path']}")
            print(f"创建: {create_t} | 修改: {mod_t}")
            print("-" * 60)

    # 报告保存到扫描目标文件夹内
    report_name = f"文件夹扫描报告_{time_suffix}.txt"
    report_path = get_unique_path(target / report_name)

    with open(report_path, "w", encoding="utf-8") as f:
        scan_mode = "（包含隐藏/系统文件）" if choose_hidden == "y" else "（已过滤隐藏/系统文件）"
        f.write(f"===== 文件夹扫描汇总报告 {scan_mode} =====\n")
        f.write(f"扫描根目录：{target}\n")
        f.write(f"扫描时间：{scan_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"子文件夹总数：{dir_count} 个\n")
        f.write(f"有效文件总数：{len(all_files)} 个\n")
        f.write(f"读取失败文件：{read_fail_count} 个\n")
        f.write(f"总占用空间：{format_size(total_byte)}\n\n")

        f.write("===== 文件后缀分类统计 =====\n")
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

    print(f"\n==================== 扫描完成 ====================")
    print(f"根目录子文件夹：{dir_count} 个")
    print(f"扫描到文件总数：{len(all_files)} 个")
    print(f"读取失败文件：{read_fail_count} 个")
    print(f"目录总占用空间：{format_size(total_byte)}")
    print(f"完整报告已保存至：{report_path}")
