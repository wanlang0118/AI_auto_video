"""
JSON工具模块 - 提供JSON文件操作的实用工具函数
"""
import json
from pathlib import Path
from typing import Any, Union


def append_json(content: Any, file_path: Union[str, Path]) -> None:
    """
    追加内容到JSON文件
    
    如果文件不存在，创建新文件并写入内容
    如果文件存在且包含列表，将内容追加到列表中
    如果文件存在且包含字典，将内容与现有字典合并
    
    Args:
        content: 需要添加的JSON内容（字典、列表或其他可序列化对象）
        file_path: JSON文件路径
        
    Raises:
        ValueError: 当内容无法序列化时抛出异常
        IOError: 当文件读写失败时抛出异常
    """
    file_path = Path(file_path)
    
    # 确保目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 检查文件是否存在
        if file_path.exists():
            # 读取现有内容
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    # 文件为空或格式错误，当作新文件处理
                    existing_data = None
        else:
            existing_data = None
        
        # 根据现有数据类型决定如何追加
        if existing_data is None:
            # 文件不存在或为空，直接写入新内容
            new_data = content
        elif isinstance(existing_data, dict):
            # 现有数据为字典，合并内容
            if isinstance(content, dict):
                new_data = {**existing_data, **content}
            else:
                # 如果新内容不是字典，但现有是字典，将新内容添加到字典中
                new_data = existing_data.copy()
                # 使用自动生成的键名或添加到特定字段
                if isinstance(content, list):
                    new_data["additional_data"] = content
                else:
                    new_data["additional_data"] = [content]
        elif isinstance(existing_data, list):
            # 现有数据为列表，追加新内容
            if isinstance(content, list):
                new_data = existing_data + content
            else:
                new_data = existing_data + [content]
        else:
            # 现有数据为其他类型，转换为数组
            if isinstance(content, list):
                new_data = [existing_data] + content
            else:
                new_data = [existing_data, content]
        
        # 写入更新后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
            
    except (IOError, OSError) as e:
        raise IOError(f"文件操作失败: {e}") from e
    except (TypeError, ValueError) as e:
        raise ValueError(f"内容无法序列化为JSON: {e}") from e


