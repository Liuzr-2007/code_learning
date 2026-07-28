# -*- coding: utf-8 -*-
"""图片合并 PDF 模块：文件夹图片批量生成 A4 PDF"""
import os
import tempfile
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image

from utils import clean_path_input, get_unique_path, logger


def folder_images_to_pdf(folder_path: str) -> None:
    """文件夹图片批量生成A4 PDF，递归子目录"""
    target = clean_path_input(folder_path)
    if not target.is_dir():
        logger.error("路径不是有效文件夹！")
        return

    output_pdf = str(get_unique_path(target / "批量照片汇总.pdf"))
    img_suffix = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    img_path_list: list[str] = []

    # 递归遍历子目录收集图片
    for root, _, files in os.walk(target):
        current_root = Path(root)
        for filename in files:
            if filename.lower().endswith(img_suffix):
                full_file_path = current_root / filename
                if full_file_path.is_file():
                    img_path_list.append(str(full_file_path))

    if len(img_path_list) == 0:
        logger.warning("未检测到任何图片文件，PDF生成失败")
        return

    # 按文件名排序，确保输出顺序稳定
    img_path_list.sort(key=lambda p: Path(p).name.lower())

    pdf = canvas.Canvas(output_pdf, pagesize=A4)
    page_width, page_height = A4

    for img_path in img_path_list:
        try:
            draw_img_path = img_path
            temp_file = None

            with Image.open(img_path) as img:
                img_width, img_height = img.size

                # 修复：RGBA PNG 转 RGB 兼容 reportlab
                if img.mode == "RGBA":
                    #Image.convert(mode)：转换图片的色彩模式
                    rgb_img = img.convert("RGB")
                    #安全创建一个唯一、空、可读写的临时文件，返回 文件描述符 fd + 文件完整路径。
                    temp_fd, temp_file = tempfile.mkstemp(suffix=".jpg")
                    #向操作系统发起调用，释放这个文件描述符资源，断开程序和临时文件的底层绑定。
                    os.close(temp_fd)
                    rgb_img.save(temp_file, "JPEG")
                    draw_img_path = temp_file

                scale_rate = min(page_height / img_height, page_width / img_width)
                draw_w = img_width * scale_rate
                draw_h = img_height * scale_rate
                X = (page_width - draw_w) / 2
                Y = (page_height - draw_h) / 2

            pdf.drawImage(draw_img_path, X, Y, width=draw_w, height=draw_h)
            pdf.showPage()

            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"图片 {img_path} 处理失败: {str(e)}")
            # 清理临时文件
            if 'temp_file' in locals() and temp_file and os.path.exists(temp_file):
                os.remove(temp_file)

    pdf.save()
    print(f"PDF生成成功，路径：{output_pdf}")
