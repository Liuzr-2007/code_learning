# -*- coding: utf-8 -*-
"""Document Summarizer 文件工具主入口

功能菜单：
  [CFI]        文件夹深度扫描统计（生成txt报告）
  [PDF]        文件夹图片批量合并PDF
  [WORD2EXCEL] 读取文件夹所有Word提取人员信息生成Excel
  [q]          退出程序
"""
import sys

from scanner import collect_folder_info
from pdf_merger import folder_images_to_pdf
from word_extractor import scan_word_folder
from excel_exporter import export_excel
from utils import clean_path_input, get_unique_path, logger


def print_menu() -> None:
    """打印主菜单"""
    print("\n==================== 文件工具主菜单 ====================")
    print("[CFI]        文件夹深度扫描统计（生成txt报告）")
    print("[PDF]        文件夹图片批量合并PDF")
    print("[WORD2EXCEL] 读取文件夹所有Word提取人员信息生成Excel")
    print("[q]          退出程序")
    print("===========================================================\n")


def word_to_excel_main(folder_input: str) -> None:
    """Word转Excel主逻辑"""
    target = clean_path_input(folder_input)
    if not target.is_dir():
        logger.error("输入路径不是有效文件夹！")
        return
    # Excel保存到目标文件夹根目录，自动编号避免覆盖
    excel_save = str(get_unique_path(target / "人员信息汇总.xlsx"))
    data = scan_word_folder(str(target))
    if len(data) == 0:
        logger.warning("文件夹内未找到任何docx文档！")
        return
    export_excel(excel_save, data)


if __name__ == "__main__":
    print_menu()
    argv_used = False  # 标记拖拽路径是否已使用

    while True:
        choice = input("请输入功能指令：").strip().upper()

        if choice == "Q":
            print("程序正常退出")
            sys.exit(0)
        elif choice == "CFI":
            if not argv_used and len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                argv_used = True
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入目标文件夹路径（可直接拖拽文件夹到窗口）：")
            collect_folder_info(folder_input)
            input("\n按回车键返回功能菜单...")
            print_menu()
        elif choice == "PDF":
            if not argv_used and len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                argv_used = True
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入图片文件夹路径：")
            folder_images_to_pdf(folder_input)
            input("\n按回车键返回功能菜单...")
            print_menu()
        elif choice == "WORD2EXCEL":
            if not argv_used and len(sys.argv) >= 2:
                folder_input = sys.argv[1]
                argv_used = True
                print(f"检测到拖拽路径：{folder_input}")
            else:
                folder_input = input("请输入存放Word文档的文件夹路径：")
            word_to_excel_main(folder_input)
            input("\n按回车键返回功能菜单...")
            print_menu()
        else:
            print("无效指令，请重新输入！")
            input("按回车键返回菜单")
            print_menu()
