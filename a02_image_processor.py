"""
图片处理模块 - 单函数全流程版
功能：
1. 传入 JSON 文件路径
2. 内部自动读取、遍历分镜、调用 API 生成图片
3. 遇到限流自动重试，强制覆盖旧图
4. 自动保存回 JSON
"""

import os
import json
import shutil
import time
import requests
from config import SILICON_API_KEY

def generate_images_from_json(json_path):
    """
    处理所有图片生成逻辑
    """
    # --- 1. 读取 JSON 文件 ---
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    scenes = data.get("scenes", [])
    base_dir = os.path.dirname(json_path)
    image_folder = os.path.join(base_dir, "images")
    # 如果文件夹存在，直接暴力删除再重建，确保彻底清空
    if os.path.exists(image_folder):
        print(f"🧹 检测到旧图片目录，正在清空: {image_folder}")
        shutil.rmtree(image_folder)  # 递归删除文件夹及其内容
    # 如果不存在创建全新的空文件夹
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    # --- 2. 循环遍历每个分镜 ---
    for index, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        # 文件名：01.png, 02.png...
        filename = f"{str(index + 1).zfill(2)}.png"
        output_path = os.path.join(image_folder, filename)
        # --- 3. API 请求与重试逻辑 ---
        url = "https://api.siliconflow.cn/v1/images/generations"
        # 优化提示词
        style_suffix = (
            "children's picture book illustration, hand-drawn crayon and colored pencil style, "
            "visible paper texture, soft rough edges, "
            "Chinese mom and Chinese child together, close parent-child interaction, "
            "mom with gentle and caring expression, child smiling and relaxed, "
            "warm family atmosphere, emotional contrast from anxious to calm, "
            "soft pastel color palette, warm light, cozy home environment, "
            "cute proportions, rounded shapes, pop mart inspired but flatter illustration style, "
            "handmade feel, scribble details, no realism, "
            "high detail illustration, consistent style"
        )

        full_prompt = f"{prompt}, {style_suffix}"
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": full_prompt,
            "image_size": "1024x576",
            "num_images": 1
        }
        headers = {
            "Authorization": f"Bearer {SILICON_API_KEY}",
            "Content-Type": "application/json"
        }
        max_retries = 5
        generate_success = False
        for attempt in range(max_retries):
            print(f"🎨 [{index+1}/{len(scenes)}] 正在生成: {filename} (第 {attempt + 1} 次)...")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            # >>> 情况 A: 成功 <<<
            if response.status_code == 200:
                image_url = response.json().get('data', [{}])[0].get('url')
                if image_url:
                    # 下载并强制覆盖保存
                    img_data = requests.get(image_url).content
                    with open(output_path, 'wb') as handler:
                        handler.write(img_data)
                    # 更新内存中的 scene 对象
                    scene["image_path"] = output_path
                    generate_success = True
                    # 简单的防并发延时
                    time.sleep(1)
                    break # 跳出重试循环，处理下一张图
            # >>> 情况 B: 失败 (处理限流) <<<
            else:
                error_msg = response.text
                if "50604" in error_msg or "limit reached" in error_msg:
                    print(f"⚠️ 触发限流，暂停 60 秒...")
                    for i in range(60, 0, -5):
                        print(f"   还剩 {i} 秒...", end="\r")
                        time.sleep(5)
                    print("\n🔄 重试中...")
                    continue # 重试
                else:
                    print(f"❌ API 错误: {response.status_code} - {error_msg}")
                    break # 非限流错误，直接放弃这张图
        if not generate_success:
            print(f"❌ 第 {index+1} 张图片生成失败，已跳过。")

    # --- 4. 循环结束后，统一保存 JSON ---
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 单元测试入口 ---
if __name__ == "__main__":
    # 直接调用这个函数即可
    generate_images_from_json("output_videos/text.json")