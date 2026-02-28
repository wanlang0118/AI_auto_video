"""
音频处理模块 - 极致精简版
功能：直接在主函数中完成 TTS 生成、时长获取和 JSON 更新，无任何辅助函数。
"""

import json
import os
import asyncio
import shutil
import edge_tts
import requests
from moviepy.editor import AudioFileClip

from config import SILICON_API_KEY


def generate_audio_from_json(json_path):
    """
    线性执行所有音频生成逻辑
    """
    # --- 1. 读取配置与清理目录 ---
    # 读取 JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    scenes = data.get("scenes", [])
    # 确定路径
    base_dir = os.path.dirname(json_path)
    audio_folder = os.path.join(base_dir, "audio")
    # 暴力清空旧目录
    if os.path.exists(audio_folder):
        print(f"🧹 清空旧目录: {audio_folder}")
        shutil.rmtree(audio_folder)
    # 创建新目录
    os.makedirs(audio_folder)
    print(f"🎙️ 开始为 {len(scenes)} 个分镜生成音频...")
    # --- 2. 核心循环：生成 -> 测时长 -> 记数据 ---
    current_timestamp = 0.0
    for index, scene in enumerate(scenes):
        # 提取文本
        text = scene.get("en", "")
        # 构造文件名
        filename = f"{str(index + 1).zfill(2)}.mp3"
        file_path = os.path.join(audio_folder, filename)
        print(f"   [{index + 1}/{len(scenes)}] 处理: {filename} ...")
        # 核心修改 A：直接生成音频，不定义函数
        # 1. 创建 TTS 对象 (参数: 文本, 语音角色)
        # 注意：第二个参数是角色名 "en-US-AnaNeural"，不是路径！
        duration = 0.0
        generation_success = False  # 标记是否生成成功

        url = "https://api.siliconflow.cn/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {SILICON_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "fishaudio/fish-speech-1.5",  # 使用 Fish Audio 模型
            "input": text,
            "voice": "fishaudio/fish-speech-1.5:bella",  # 这是一个非常自然的男声，或者换其他 ID
            # 注意：如果 SiliconFlow 还没有完全开放这个 endpoint，会回退到 EdgeTTS
            "response_format": "mp3",
            "sample_rate": 32000
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"❌ API 请求失败: {response.status_code}")
            print(f"❌ 错误信息: {response.text}")
            raise Exception("音频生成失败，程序终止")

        with open(file_path, "wb") as audio_file:
            audio_file.write(response.content)

        with AudioFileClip(str(file_path)) as audio:
            duration = audio.duration


        # 核心修改 C：更新数据
        scene["audio_path"] = str(file_path)
        scene["duration"] = round(duration, 2)
        scene["start_time"] = round(current_timestamp, 2)
        scene["end_time"] = round(current_timestamp + duration, 2)
        # 累加时间
        current_timestamp += duration
    # 记录总时长
    data["total_duration"] = round(current_timestamp, 2)
    # --- 3. 保存结果 ---
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 处理完成，总时长: {data['total_duration']}秒")


# --- 运行入口 ---
if __name__ == "__main__":
    generate_audio_from_json("output_videos/text.json")