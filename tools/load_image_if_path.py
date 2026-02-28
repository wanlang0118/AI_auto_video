from typing import  Any  # 导入类型提示所需类型
from pathlib import Path  # 导入路径处理模块
from PIL import Image, ImageDraw  # 导入图像处理库和绘图模块

def load_image_if_path(image_or_path) :
    """
    如果传入的是路径则加载为PIL Image，若已是Image则直接返回。
    参数:
        image_or_path: 图像对象或图像文件路径
    返回:
        Image.Image: PIL图像对象
    异常:
        FileNotFoundError: 当文件路径不存在时
        ValueError: 当输入类型不合法时
    """
    # 检查输入是否为字符串或Path对象（即文件路径）
    if isinstance(image_or_path, (str, Path)):
        img_path = Path(image_or_path)  # 转换为Path对象便于操作
        if not img_path.exists():  # 检查文件是否存在
            raise FileNotFoundError(f"图像文件不存在: {img_path}")  # 文件不存在时抛出异常
        return Image.open(img_path)  # 使用PIL打开图像文件
    # 检查输入是否已经是PIL图像对象
    if isinstance(image_or_path, Image.Image):
        return image_or_path  # 直接返回图像对象
    # 输入类型不合法时抛出异常
    raise ValueError("输入必须是图像路径或PIL Image对象")