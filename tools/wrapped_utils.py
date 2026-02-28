from typing import List
from PIL import  ImageFont


def get_wrapped_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """
    基于真实像素宽度的智能换行算法

    Args:
        text: 需要换行的文本内容
        font: PIL字体对象
        max_width: 最大宽度限制（像素）

    Returns:
        换行后的文本行列表

    Raises:
        ValueError: 当输入参数无效时抛出异常
    """
    if max_width <= 0:
        raise ValueError("最大宽度必须大于0")

    lines = []
    if not text or not text.strip():
        return lines

    current_line = ""

    # 遍历每一个字符进行智能换行
    for char in text:
        # 试探性加入字符，检查是否超宽
        test_line = current_line + char
        text_width = font.getlength(test_line)

        if text_width <= max_width:
            # 未超宽，加入当前行
            current_line = test_line
        else:
            # 超宽处理：优先保护英文单词完整性
            last_space_index = current_line.rfind(" ")

            if last_space_index == -1 or char == " ":
                # 无空格分割点或当前字符为空格，直接换行
                if current_line:  # 避免空行
                    lines.append(current_line)
                current_line = char if char != " " else ""
            else:
                # 英文单词回溯，避免单词被切断
                lines.append(current_line[:last_space_index])
                current_line = current_line[last_space_index + 1:] + char

    # 添加最后一行
    if current_line.strip():
        lines.append(current_line)

    return lines