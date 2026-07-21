# -*- coding: utf-8 -*-
import os
import re
import sys
import ctypes
import datetime
from pathlib import Path
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

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

def get_file_attributes(file_path: Path) -> int:
    """获取Windows文件属性标志，失败返回-1"""
    try:
        return kernel32.GetFileAttributesW(str(file_path))
    except Exception:
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
    except Exception as e:
        return f"读取失败: {str(e)}"

def collect_folder_info(folder_input: str):
    """遍历文件夹生成扫描统计txt报告"""
    clean_path = folder_input.strip().strip('"').strip("'")
    target = Path(clean_path)

    if not target.is_dir():
        print(f"错误：路径「{target}」不是有效文件夹！")
        return

    while True:
        choose_hidden = input("是否一并查询隐藏/系统文件？输入 y 包含，n 过滤：").strip().lower()
        if choose_hidden in ("y", "n"):
            break
        print("无效输入，请输入 y 或 n")

    print(f"\n==========开始扫描目录: {target} ==========")
    all_files = []
    suffix_counter = defaultdict(int)
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

            try:
                stat_info = file_full.stat()
                file_size = stat_info.st_size
                total_byte += file_size
                err_msg = None
            except (PermissionError, FileNotFoundError, OSError) as e:
                file_size = 0
                err_msg = str(e)
                read_fail_count += 1

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
            print(f"【文件】{file_info['name']} | {file_info['size_str']}")
            print(f"完整路径: {file_info['path']}")
            print(f"创建: {create_t} | 修改: {mod_t}")
            print("-" * 60)

    time_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"文件夹扫描报告_{time_suffix}.txt"

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
    print(f"完整报告已保存至：{os.path.abspath(report_name)}")

def folder_images_to_pdf(folder_path):
    """文件夹图片批量生成A4 PDF"""
    clean_path = folder_path.strip().strip('"').strip("'")
    target = Path(clean_path)
    if not target.is_dir():
        print("路径不是有效文件夹！")
        return
    output_pdf = str(target / "批量照片汇总.pdf")
    img_suffix = (".jpg", ".jpeg", ".png")
    img_path_list = []

    for filename in os.listdir(target):
        full_file_path = target / filename
        if filename.lower().endswith(img_suffix) and full_file_path.is_file():
            img_path_list.append(str(full_file_path))

    if len(img_path_list) == 0:
        print("未检测到任何图片文件，PDF生成失败")
        return

    pdf = canvas.Canvas(output_pdf, pagesize=A4)
    page_width, page_height = A4

    for img_path in img_path_list:
        try:
            img = Image.open(img_path)
            img_width, img_height = img.size
            scale_rate = min(page_height / img_height, page_width / img_width)
            draw_w = img_width * scale_rate
            draw_h = img_height * scale_rate
            X = (page_width - draw_w) / 2
            Y = (page_height - draw_h) / 2
            pdf.drawImage(img_path, X, Y, width=draw_w, height=draw_h)
            pdf.showPage()
        except Exception as e:
            print(f"图片 {img_path} 处理失败: {str(e)}")
    pdf.save()
    print(f"PDF生成成功，路径：{output_pdf}")

# ====================== Word提取配置区 ======================
FIELDS = [
    ("姓名", ["姓名", "姓 名"]),
    ("性别", ["性别", "性 别"]),
    ("年龄", ["年龄"]),
    ("身份证号", ["身份证", "身份证号", "证件号"]),
    ("手机号", ["电话", "手机号", "联系电话"]),
    ("住址", ["住址", "地址", "家庭住址"]),
    ("学历", ["学历"]),
    ("工作单位", ["单位", "工作单位"])
]
# ==========================================================

def extract_word_info(file_path):
    """读取单个docx提取人员信息，增加异常捕获"""
    try:
        doc = Document(file_path)
    except Exception as e:
        print(f"警告：文档 {os.path.basename(file_path)} 损坏/无法读取，跳过：{e}")
        empty_data = {"文档名称": os.path.basename(file_path)}
        for col, _ in FIELDS:
            empty_data[col] = ""
        return empty_data

    content = ""
    # 读取段落
    for p in doc.paragraphs:
        content += p.text + "\n"
    # 读取表格
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                content += cell.text + "\n"

    info = {"文档名称": os.path.basename(file_path)}
    # 优化正则：匹配【关键词：内容】，换行/下一个关键词截止
    all_keys = []
    for _, kl in FIELDS:
        all_keys.extend(kl)
    key_pattern_str = "|".join([re.escape(k) for k in all_keys])

    for col_name, keywords in FIELDS:
        val = ""
        for key in keywords:
            # 精准匹配：关键词：xxx，直到换行或下一个字段关键词
            pattern = re.compile(rf"{re.escape(key)}[：:]\s*(.+?)(?=\n|({key_pattern_str})[：:])", re.S)
            res = pattern.search(content)
            if res:
                val = res.group(1).strip()
                break
        info[col_name] = val
    return info

def scan_word_folder(folder_path):
    """遍历文件夹收集全部docx"""
    word_files = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".docx"):
                full_p = os.path.join(root, f)
                word_files.append(full_p)
    all_data = []
    for file in word_files:
        print(f"正在读取：{os.path.basename(file)}")
        data = extract_word_info(file)
        all_data.append(data)
    return all_data

def export_excel(save_path, data_list):
    """导出汇总Excel，修复拼写bug"""
    wb = Workbook()
    ws = wb.active
    ws.title = "人员信息汇总"

    headers = ["文档名称"] + [item[0] for item in FIELDS]
    ws.append(headers)

    # 表头样式
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    head_font = Font(bold=True)
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = head_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # 写入数据行
    for row_data in data_list:
        row = [row_data["文档名称"]] + [row_data[col] for col, _ in FIELDS]
        ws.append(row)

    # 自动列宽（修复colums/maax_len拼写错误）
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_len + 4

    wb.save(save_path)
    print(f"\nExcel文件已保存至：{save_path}")

def word_to_excel_main(folder_input):
    """Word转Excel主逻辑"""
    clean_path = folder_input.strip().strip('"').strip("'")
    target = Path(clean_path)
    if not target.is_dir():
        print("输入路径不是有效文件夹！")
        return
    # Excel保存到目标文件夹根目录
    excel_save = str(target / "人员信息汇总.xlsx")
    data = scan_word_folder(str(target))
    if len(data) == 0:
        print("文件夹内未找到任何docx文档！")
        return
    export_excel(excel_save, data)

if __name__ == "__main__":
    print("\n==================== 文件工具主菜单 ====================")
    print("[CFI]        文件夹深度扫描统计（生成txt报告）")
    print("[PDF]        文件夹图片批量合并PDF")
    print("[WORD2EXCEL] 读取文件夹所有Word提取人员信息生成Excel")
    print("[q]          退出程序")
    print("===========================================================\n")

    while True:
        choice = input("请输入功能指令：").strip().upper()

        if choice == "Q":
            print("程序正常退出")
            sys.exit(0)
        elif choice == "CFI":
            if len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入目标文件夹路径（可直接拖拽文件夹到窗口）：")
            collect_folder_info(folder_input)
            input("\n按回车键返回功能菜单...")
        elif choice == "PDF":
            if len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入图片文件夹路径：")
            folder_images_to_pdf(folder_input)
            input("\n按回车键返回功能菜单...")
        elif choice == "WORD2EXCEL":
            if len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入存放Word文档的文件夹路径：")
            word_to_excel_main(folder_input)
            input("\n按回车键返回功能菜单...")
        else:
            print("无效指令，请重新输入！")
            input("按回车键返回菜单")

#仍有许多问题，例如：
#只解决生成excel文件的问题，但只能单独读取文件中的一个人的信息
#无法对上下级包含关系做出反应
#可能需要引入ai？