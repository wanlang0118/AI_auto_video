"""
内容生成模块 - 函数式版
功能：
1. 调用 LLM 生成分镜列表 (scenes)
2. 自动拼接全文 (full_story)
3. 保存为最终 JSON
"""

import json
import os
from openai import OpenAI
from config import SILICON_API_KEY, BASE_URL, VIDEO_THEME, OUTPUT_FOLDER

def generate_video_script(theme: str):
    """
    核心函数：根据主题生成脚本、拼接全文并保存
    """
    # 1. 初始化客户端
    client = OpenAI(api_key=SILICON_API_KEY, base_url=BASE_URL)
    # 2. 准备 Prompt
    # 定义系统级提示词 (System Prompt) - 确立人设、底层逻辑和格式约束
    system_prompt = """
    你是一位拥有百万粉丝的“反焦虑”育儿博主，也是一个英语并不完美的二胎宝妈。
    你的粉丝是普通中国妈妈：英语不好、时间很少、容易自责。
    
    【你的创作底层原则】
    1. 你永远站在“妈妈这边”，先安抚情绪，再给方法。
    2. 你反对鸡娃英语，只教“孩子听得懂、妈妈说得出口”的话。
    3. 你的视频目标不是教会英语，而是让妈妈“今天敢开口”。
    
    【短视频强制结构（6–8 个分镜，必须具体）】
    - 分镜 1（0–2 秒）：一个【极其具体的崩溃场景】  
      例：早上出门，孩子穿鞋磨蹭，你已经喊了 3 遍。
    - 分镜 2（2–4 秒）：妈妈真实情绪独白（第一人称）  
      例：那一刻我真的很想吼。
    - 分镜 3（错误示范）：一个【中国妈妈常见但无效的反应】  
      明确写 “Don’t say …”，要真实、要尴尬。
    - 分镜 4（转折）：你意识到“不是孩子的问题”。
    - 分镜 5（唯一金句）：只给【一句】英文，3–6 个单词，温柔、口语、亲子真实表达。
    - 分镜 6（效果）：孩子的反应（动了/笑了/回应了）。
    - 分镜 7（情绪安抚）：对妈妈说一句“你已经做得很好了”。
    - 分镜 8（轻引导）：温柔引导收藏或关注，不强推。
    
    【语言与画面要求】
    - 中文：第一人称，口语化，像在和闺蜜说话。
    - 英文：极简、可立刻模仿，避免命令式。
    - 画面感：温馨、生活化、亲子互动特写。
    
    【严格要求】
    - 不讲语法、不解释规则。
    - 不出现“教育专家”“研究表明”。
    - 只围绕一个生活场景。
    - 严格输出 JSON，不要多余说明。
    """

    # 定义用户级提示词 (User Prompt) - 传入主题并强化具体要求
    user_prompt = f"""
    请根据主题 "{theme}" 生成一个【抖音 / 小红书】短视频脚本，并严格按照下述要求输出【完整 JSON】。
    
    【整体创作目标】
    - 面向：中国普通宝妈 + 中国宝宝。
    - 风格：反焦虑、温柔、不鸡娃。
    - 目标：用一句真正“有用”的英文，缓解一个真实育儿小崩溃。
    
    【内容硬性要求】
    - 只解决【一个】具体生活场景（如出门、吃饭、洗澡、睡觉）。
    - 英文必须简单、口语、幼儿可理解，妈妈可立刻模仿。
    - 所有 Scene **必须包含英文台词（en）**，且每一句英文都必须“有用”（情绪表达 / 互动 / 转折 / 引导）。
    
    【Title 要求】
    - title_en：3–5 个英文单词，表达孩子不配合或妈妈崩溃的状态（不超过 15 个字母）。
    - title_cn：13 个字以内，必须包含情绪或冲突（如“崩溃 / 忍不住 / 别再”）。
    
    【Scenes 分镜规则（固定 8 个，顺序不可变）】
    
    1. Scene 1（崩溃现场）
       - en：简短英文，表达“着急 / 来不及 / 情绪紧绷”。
       - cn：第一人称，具体动作的崩溃瞬间。
       - image_prompt：Chinese mom anxious + Chinese child not cooperating.
    
    2. Scene 2（情绪共鸣）
       - en：英文情绪表达（如 tired / overwhelmed / need a breath）。
       - cn：妈妈真实内心感受。
       - image_prompt：情绪特写，焦虑但克制。
    
    3. Scene 3（错误示范 · 强制）
       - en：必须以 "Don't say:" 开头，使用命令式或复杂英语。
       - cn：说明这种说法为什么没用。
       - image_prompt：孩子抗拒或更磨蹭。
    
    4. Scene 4（认知转折）
       - en：英文认知转折（如 He is not ready / It’s not his fault）。
       - cn：妈妈意识到问题不在孩子。
       - image_prompt：妈妈表情开始变柔和。
    
    5. Scene 5（唯一金句 · 强制）
       - en：必须以 "Try to say:" 开头，仅一句，3–6 个词，亲子高频口语。
       - cn：一句话说明为什么这句更温柔、更有效。
       - image_prompt：妈妈温柔说话，孩子注意到。
    
    6. Scene 6（效果出现）
       - en：孩子的简单回应或配合。
       - cn：孩子情绪或行为的变化。
       - image_prompt：孩子开心 / 配合。
    
    7. Scene 7（安抚妈妈）
       - en：温柔的肯定句，给妈妈情绪支持。
       - cn：不评判、不焦虑的安抚。
       - image_prompt：温馨亲子互动。
    
    8. Scene 8（轻引导结尾）
       - en：简单的引导收藏 / 记住的话。
       - cn：温柔结尾，引导收藏或关注。
       - image_prompt：治愈、安静的家庭画面。
    
    【严格限制（非常重要）】
    - “Don't say:” 只能出现 1 次。
    - “Try to say:” 只能出现 1 次。
    - 不讲语法、不解释规则。
    - 不使用教育专家或理论化语言。
    - 每个 Scene 必须包含 en / cn / image_prompt，不得缺失。
    - image_prompt 必须为英文。
    - 严格只输出 JSON，不要添加任何说明或多余文字。
    
    【JSON 输出结构】
    {{
      "title_en": "...",
      "title_cn": "...",
      "scenes": [·
        {{
          "en": "...",
          "cn": "...",
          "image_prompt": "..."
        }}
      ]
    }}

    """

    # 调用 API (直接调用，无异常处理)
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,  # 稍微降低一点温度，保证格式稳定
        response_format={"type": "json_object"}  # 如果模型支持，强制 JSON 模式更安全
    )

    # 获取内容
    content = response.choices[0].message.content
    # 4. 清洗数据 (防止 AI 返回 ```json 包裹)
    clean_content = content.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean_content)
    # 5. 拼接全文 (Story Stitching)
    scenes = data.get("scenes", [])
    if scenes:
        # 拼接英文：用空格连接
        full_story_en = " ".join([s["en"] for s in scenes])
        # 拼接中文
        full_story_cn = "".join([s["cn"] for s in scenes])
        # 写入字典
        data["story_en"] = full_story_en
        data["story_cn"] = full_story_cn
    # 6. 保存文件
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    # 统一保存为 text.json，方便后续模块读取
    file_path = os.path.join(OUTPUT_FOLDER, "text.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


# --- 主程序入口 ---
if __name__ == "__main__":
    # 直接调用函数
    script = generate_video_script("哈喽世界")
