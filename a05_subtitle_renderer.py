"""
视频合成模块 - 最终版
功能：
1. 修复 PIL.Image.ANTIALIAS 报错
2. 修复 moviepy 导入错误
3. 实现三段式布局：上部(插图) + 中部(全文) + 下部(字幕)
4. 导出最终 MP4
"""

import os
import json
import numpy as np

# --- 🚨 关键修复：必须放在 moviepy 导入之前或紧随其后 ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
# -----------------------------------------------------

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, ImageClip, TextClip, CompositeVideoClip,
    AudioFileClip, ColorClip, concatenate_audioclips
)
from config import OUTPUT_FOLDER, VIDEO_THEME

# 布局配置
VIDEO_W, VIDEO_H = 1080, 1920

def create_subtitle_image(en_text, cn_text, width=900, height=250):
    """
    使用 PIL 绘制底部的字幕气泡
    """
    # 创建透明画布
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 配置
    bg_color = (255, 105, 180, 255) # 粉色背景 #FF69B4
    text_color = (255, 255, 255, 255) # 白色文字

    # 尝试加载字体
    try:
        font_en = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
    except:
        font_en = ImageFont.load_default()

    try:
        font_cn = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 55)
    except:
        font_cn = ImageFont.load_default()

    # 画圆角矩形背景
    draw.rounded_rectangle((0, 0, width, height), radius=30, fill=bg_color)

    # 绘制英文 (居中)
    y_en = 50
    if en_text:
        bbox_en = font_en.getbbox(en_text)
        if bbox_en:
            w_en = bbox_en[2] - bbox_en[0]
            x_en = (width - w_en) / 2
            draw.text((x_en, y_en), en_text, font=font_en, fill=text_color)

    # 绘制中文 (居中)
    if cn_text:
        bbox_cn = font_cn.getbbox(cn_text)
        if bbox_cn:
            w_cn = bbox_cn[2] - bbox_cn[0]
            x_cn = (width - w_cn) / 2
            y_cn = y_en + 60 if en_text else 50
            draw.text((x_cn, y_cn), cn_text, font=font_cn, fill=text_color)

    return np.array(img)

def safe_resize_image(image_path, target_width):
    """
    安全地调整图片大小
    """
    try:
        target_width = int(target_width)  # 确保是整数
        with Image.open(image_path) as img:
            # if img.mode in ('RGBA', 'LA', 'P'):
            #     background = Image.new('RGB', img.size, (255, 255, 255))（白色背景）
            #     if img.mode == 'RGBA':
            #         background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
            #     else:
            #         background.paste(img)
            #     img = background
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # 2. 计算新高度
            ratio = target_width / img.width
            new_height = int(img.height * ratio)

            # 3. 调整大小 (PIL 支持直接缩放 RGBA)
            img_resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)

            # 4. 返回包含 Alpha 通道的数组 (MoviePy 会自动识别)
            return np.array(img_resized)
    except Exception as e:
        print(f"⚠️ 无法处理图片 {image_path}: {e}")
        return np.zeros((target_width, target_width, 3), dtype=np.uint8)

def compose_video():
    print("🎬 开始合成视频...")

    # 1. 读取数据
    json_path = os.path.join(OUTPUT_FOLDER, "text.json")
    if not os.path.exists(json_path):
        print(f"❌ 找不到脚本文件: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get("scenes", [])
    full_text_path = data.get("full_text_page_path", "")

    if not scenes:
        print("❌ 没有场景数据")
        return

    # 2. 准备基础图层

    # --- Layer 0: 背景层 ---
    bg_color = (250, 245, 230) # 米黄色
    bg_clip = ColorClip(size=(VIDEO_W, VIDEO_H), color=bg_color)

    # --- Layer 1: 中间全文 (静态层) ---
    mid_clip = None
    if os.path.exists(full_text_path):
        try:
            # 调整宽度为屏幕的 87% 以留出边距
            mid_img_array = safe_resize_image(full_text_path, int(VIDEO_W * 0.87))
            mid_clip = ImageClip(mid_img_array)
            # 放置在屏幕正中间
            mid_clip = mid_clip.set_position(('center', 1920 * 0.4))
            print(f"✅ 已添加中间全文层: {full_text_path}")
        except Exception as e:
            print(f"⚠️ 中间全文层添加失败: {e}")
    else:
        print("⚠️ 未找到全文图片，跳过中间层")

    # --- Layer 2 & 3: 动态插图 + 动态字幕 ---
    top_clips = []
    subtitle_clips = []
    audio_clips = []
    total_duration = 0.0

    print(f"🔄 正在处理 {len(scenes)} 个分镜...")

    for i, scene in enumerate(scenes):
        print(f"  处理场景 {i+1}/{len(scenes)}...")

        img_path = scene.get("image_path", "")
        audio_path = scene.get("audio_path", "")
        duration = scene.get("duration", 3.0)
        en_text = scene.get("en", "")
        cn_text = scene.get("cn", "")

        start_time = total_duration
        current_duration = duration

        # A. 音频
        if os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path)
                current_duration = max(duration, audio.duration)
                audio = audio.set_start(start_time)
                audio_clips.append(audio)
            except Exception as e:
                print(f"    ⚠️ 音频错误: {e}")


        # B. 处理顶部插图 (16:9, 内联圆角 + 动态缩放)
        if os.path.exists(img_path):
            try:
                # 1. 调整大小 (稍微缩小到 1000，留出边距让圆角更明显)
                target_w = 1000
                img_array = safe_resize_image(img_path, target_w)

                # --- 🟢 开始：内联圆角处理逻辑 ---
                # 将 numpy 数组转回 PIL 图片以便画图
                pil_img = Image.fromarray(img_array).convert("RGBA")

                # 创建透明遮罩 (L模式: 0=透明, 255=不透明)
                mask = Image.new('L', pil_img.size, 0)
                draw = ImageDraw.Draw(mask)

                # 画一个白色的圆角矩形 (半径 40)
                draw.rounded_rectangle([(0, 0), pil_img.size], radius=40, fill=255)

                # 将遮罩应用到图片
                pil_img.putalpha(mask)

                # 转回 numpy 数组给 MoviePy 使用
                img_array_rounded = np.array(pil_img)
                # --- 🔴 结束：内联圆角处理逻辑 ---

                # 2. 创建 Clip
                img_clip = ImageClip(img_array_rounded).set_duration(current_duration).set_start(start_time)


                # 3. 添加动态缩放 (Ken Burns Effect)
                # 注意：缩放必须在 fadein 之前或者之后都可以，但通常先缩放逻辑比较清晰
                img_clip = img_clip.resize(lambda t: 1 + 0.04 * t)

                # 4. 关键修改：添加淡入效果 (0.5秒)
                # 这样每张图出现时，会从透明(显示背景米色)慢慢浮现，非常柔和
                img_clip = img_clip.crossfadein(0.5)

                # 4. 设置位置 (距离顶部 100 像素)
                img_clip = img_clip.set_position(('center', 100))

                top_clips.append(img_clip)
                print(f"    ✓ 图片加载成功 (圆角+动态缩放)")
            except Exception as e:
                print(f"    ⚠️ 图片处理错误: {e}")

        # C. 底部字幕 (贴底)
        if en_text or cn_text:
            try:
                sub_img_np = create_subtitle_image(en_text, cn_text)
                sub_clip = ImageClip(sub_img_np).set_duration(current_duration).set_start(start_time)
                # 放在底部 (y=1550)
                sub_clip = sub_clip.set_position(('center', 1550))
                subtitle_clips.append(sub_clip)
            except Exception as e:
                print(f"    ⚠️ 字幕错误: {e}")

        total_duration += current_duration

    # 3. 组合图层
    bg_clip = bg_clip.set_duration(total_duration)
    layers = [bg_clip]

    if mid_clip:
        mid_clip = mid_clip.set_duration(total_duration)
        layers.append(mid_clip)

    layers.extend(top_clips)
    layers.extend(subtitle_clips)

    # 4. 渲染
    print("🎨 正在合成图层...")
    final_video = CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))

    if audio_clips:
        print("🔊 正在合并音频...")
        final_video = final_video.set_audio(concatenate_audioclips(audio_clips))

    output_filename = os.path.join(OUTPUT_FOLDER, "video.mp4")
    print(f"💾 正在导出视频 ({total_duration:.2f}s)...")

    final_video.write_videofile(
        output_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="video.m4a",
        remove_temp=True,
        threads=4
    )
    print(f"✅ 完成！文件: {output_filename}")

if __name__ == "__main__":
    compose_video()