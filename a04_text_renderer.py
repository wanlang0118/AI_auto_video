"""
文本绘图模块 - 极简版
功能：读取JSON数据 -> 计算排版 -> 绘制透明底文本图 -> 保存并更新路径
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
from config import OUTPUT_FOLDER
from tools.wrapped_utils import get_wrapped_text

def generate_full_text_image(json_path):
    """
    生成全文图片的核心函数
    直接执行，不包含冗余的错误捕捉
    """
    # 1. 样式与配置 (扁平化管理)
    CANVAS_WIDTH = 900
    PADDING = 50
    LINE_SPACING = 30         # 正文行间距
    BLOCK_SPACING = 20        # 标题间距
    BODY_MARGIN_TOP = 50      # 正文距离上方距离
    # 颜色配置
    COLOR_TITLE_EN = "#008B8B"  # 深青色
    COLOR_TITLE_CN = "#333333"  # 深灰色
    COLOR_BODY = "#000000"      # 纯黑
    BG_COLOR = (0, 0, 0, 0)     # 完全透明
    # 字体路径 (Windows默认)
    FONT_PATH_EN = "C:/Windows/Fonts/arial.ttf"
    FONT_PATH_CN = "C:/Windows/Fonts/msyh.ttc"

    # 2. 读取数据与加载资源
    # 读取数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    title_en = data.get("title_en", "")
    title_cn = data.get("title_cn", "")
    story_en = data.get("story_en", "")
    # 加载字体对象
    font_title = ImageFont.truetype(FONT_PATH_EN, 80)
    font_subtitle = ImageFont.truetype(FONT_PATH_CN, 60)
    font_body = ImageFont.truetype(FONT_PATH_EN, 45)
    # 3. 计算排版尺寸
    # 计算正文最大宽度
    max_text_width = CANVAS_WIDTH - (PADDING * 2)
    # 计算英文标题尺寸
    bbox_te = font_title.getbbox(title_en)
    h_title = bbox_te[3] - bbox_te[1]
    w_title = font_title.getlength(title_en)
    # 计算中文标题尺寸
    bbox_tc = font_subtitle.getbbox(title_cn)
    h_subtitle = bbox_tc[3] - bbox_tc[1]
    w_subtitle = font_subtitle.getlength(title_cn)
    # 计算正文折行与高度 (核心逻辑)
    body_lines = get_wrapped_text(story_en, font_body, max_text_width)
    # 获取单行高度
    bbox_b = font_body.getbbox("Ay")
    h_body_line = bbox_b[3] - bbox_b[1]
    # 计算正文总高度 = 行数 * (行高 + 间距)
    h_body_total = len(body_lines) * (h_body_line + LINE_SPACING)
    # 计算画布总高度 (累加所有元素和间距)
    canvas_height = (
        PADDING +
        h_title + BLOCK_SPACING +
        h_subtitle + BODY_MARGIN_TOP +
        h_body_total +
        PADDING
    )
    # 4. 绘制图像
    img = Image.new('RGBA', (CANVAS_WIDTH, int(canvas_height)), BG_COLOR)
    draw = ImageDraw.Draw(img)
    current_y = PADDING
    # A. 绘制英文标题 (水平居中)
    x_te = (CANVAS_WIDTH - w_title) / 2
    draw.text((x_te, current_y), title_en, font=font_title, fill=COLOR_TITLE_EN)
    current_y += h_title + BLOCK_SPACING
    # B. 绘制中文标题 (水平居中)
    x_tc = (CANVAS_WIDTH - w_subtitle) / 2
    draw.text((x_tc, current_y), title_cn, font=font_subtitle, fill=COLOR_TITLE_CN)
    current_y += h_subtitle + BODY_MARGIN_TOP
    # C. 绘制正文 (左对齐)
    for line in body_lines:
        draw.text((PADDING, current_y), line, font=font_body, fill=COLOR_BODY)
        current_y += h_body_line + LINE_SPACING
    # 5. 保存结果
    # 确定路径
    base_dir = os.path.dirname(json_path)
    output_path = os.path.join(base_dir, "主文本.png")
    # 保存图片
    img.save(output_path)
    print(f"✅ 全文图片生成完毕: {output_path}")
    # 回写 JSON
    data["full_text_page_path"] = output_path
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 测试入口 ---
if __name__ == "__main__":
    test_json_path = os.path.join(OUTPUT_FOLDER, "text.json")
    generate_full_text_image(test_json_path)