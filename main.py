#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
from config import VIDEO_THEME, OUTPUT_FOLDER

# 导入各模块的核心函数
from a01_content_generator import generate_video_script
from a02_image_processor import generate_images_from_json
from a03_audio_processor import generate_audio_from_json
from a04_text_renderer import generate_full_text_image
from a05_subtitle_renderer import compose_video


def main():
    start_time = time.time()
    json_path = os.path.join(OUTPUT_FOLDER, "text.json")

    print(f"🚀 开始制作视频流水线：{VIDEO_THEME}\n")
    # 定义执行步骤：(步骤名称, 函数对象, 参数元组)
    generate_video_script(VIDEO_THEME)
    generate_images_from_json("output_videos/text.json")
    generate_audio_from_json("output_videos/text.json")
    generate_full_text_image("output_videos/text.json")
    compose_video()


    # 结束统计
    duration = int(time.time() - start_time)
    final_video = os.path.join(OUTPUT_FOLDER, f"{VIDEO_THEME}_final.mp4")

    print("=" * 50)
    print(f"🎉 全部完成！总耗时: {duration}秒")
    if os.path.exists(final_video):
        print(f"📁 最终视频: {final_video}")
    else:
        print("⚠️ 警告: 未检测到视频文件，请检查最后一步输出。")
    print("=" * 50)


if __name__ == "__main__":
    main()