from typing import List

def str_to_array(message: str) -> List[dict]:
    """将字符串消息转换为消息数组格式。

    Parameters
    ----------
    message : str
        要转换的字符串消息

    Returns
    -------
    List[dict]
        转换后的消息数组
    """
    return [{"type": "text", "data": {"text": message}}]
