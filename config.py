# config.py - 配置文件，存放所有配置信息
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# SilicFlow API 配置
# 配置参数
# ImageMagick的所在文件夹
IMAGEMAGICK_BINARY = r"F:\ImageMagick\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
# 硅基流动的API密钥
SILICON_API_KEY = ""
# 硅基流动的API基础URL
BASE_URL = "https://api.siliconflow.cn/v1"
# 字体文件路径
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"
# 输出文件夹
OUTPUT_FOLDER = "output_videos"
# 视频主题配置
VIDEO_THEME = "我的一天"
IMG_THEME = "生日快乐"
SUBTITLE_THEME = "生日快乐字幕"
# 文件路径设置
BACKGROUND_IMAGE = "背景.png"  # 背景图片文件名