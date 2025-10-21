import re

from packaging import version
from typing import Optional, List, Dict

from mcdreforged.api.rtext import RText, RAction, RColor

from gugubot.constant.qq_emoji_map import qq_emoji_map

class McMessageBuilder:
    @staticmethod
    def build(
        forward_content: str | RText, *,
        group_name: str = "QQ",
        group_id: Optional[str] = None,
        sender: Optional[str] = None,
        receiver: Optional[str] = None
    ) -> RText:
        rtext = RText(f"[{group_name}]", color=RColor.gold)
        if group_id is not None:
            rtext = rtext.set_hover_text(group_id).set_click_event(action=RAction.copy_to_clipboard, value=group_id)
        if sender is not None:
            rtext += RText(f" [{sender}]", color=RColor.green)
        if receiver is not None:
            rtext += RText(f"[@{receiver}]", color=RColor.aqua)
        if isinstance(forward_content, RText):
            rtext += RText(" ") + forward_content
        else:
            rtext += RText(f" {forward_content}", color=RColor.white)

        return rtext
    

    @staticmethod
    def array_to_RText(
        array: List[Dict[str, Dict[str, str]]], 
        low_game_version: bool = False, 
        ChatImage: bool = False
    ) -> RText:
        process_functions = {
            "text": lambda data: RText(
                data['text'] if not low_game_version 
                else McMessageBuilder.replace_emoji_with_placeholder(data['text'])
            ),
            "at": lambda data: RText(f"[@{data['qq']}]", color=RColor.aqua),
            "image": lambda data: McMessageBuilder.process_image(data, chat_image=ChatImage),
            "record": lambda _: RText("[语音]"),
            "video": lambda _: RText("[视频]"),
            "face": lambda data: McMessageBuilder.process_face(data, low_game_version=low_game_version),
            "bface": lambda _: RText("[表情]"),
            "mface": lambda data: McMessageBuilder.process_image(data, chat_image=ChatImage),
            "sface": lambda _: RText("[表情]"),
            "rps": lambda _: RText("[猜拳]"),
            "dice": lambda _: RText("[掷骰子]"),
            "shake": lambda _: RText("[窗口抖动]"),
            "poke": lambda _: RText("[戳一戳]"),
            "anonymous": lambda _: RText("[匿名消息]"),
            "share": lambda _: RText("[链接]"),
            "contact": lambda data: RText("[推荐群]") if data.get('type') == 'group' else RText("[推荐好友]"),
            "location": lambda _: RText("[定位]"),
            "music": lambda _: RText("[音乐]"),
            "forward": lambda _: RText("[转发消息]"),
            "file": lambda _: RText("[文件]"),
            "redbag": lambda _: RText("[红包]"),
            "json": lambda data: RText(
                f"[链接:{data.get('meta', {}).get('detail_1', {}).get('desc', '')}]" \
                or f"[群公告:{data.get('prompt', '')}"
            ),
        }
        
        result = RText("")

        for message in array:
            
            message_type = message['type']
            message_data = message['data']

            result += process_functions.get(message_type, lambda x: '')(message_data)

        return result
    
    @staticmethod
    def is_low_game_version(version_string: str) -> bool:
        version_pattern = r'^\d+(\.\d+){0,2}$'
        if not re.match(version_pattern, version_string or ""):
            return True
        return version.parse(version_string or "1.12") >= version.parse("1.12")


    @staticmethod
    def replace_emoji_with_placeholder(text: str) -> str:
        # RE for emoji
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # various symbols and icons
            "\U0001F680-\U0001F6FF"  # transportation symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # geometric shapes
            "\U0001F800-\U0001F8FF"  # supplemental arrows
            "\U0001F900-\U0001F9FF"  # supplemental emoticons
            "\U0001FA00-\U0001FA6F"  # supplemental tools and objects
            "\U0001FA70-\U0001FAFF"  # supplemental cultural symbols
            "\u2600-\u26FF"          # miscellaneous symbols
            "\u2700-\u27BF"          # Dingbats
            "]+", flags=re.UNICODE
        )
        # Replace emoji with `[emoji]`
        return emoji_pattern.sub("[emoji]", text)
    

    @staticmethod
    def process_face(data: Dict[str, str], low_game_version: bool = False) -> RText:
        emoji = str(qq_emoji_map.get(data['id'], ''))

        if low_game_version:
            emoji = McMessageBuilder.replace_emoji_with_placeholder(emoji)

        return RText(f"[表情:{emoji}]") if emoji else RText("[表情]")


    @staticmethod
    def process_image(data: Dict[str, str], chat_image: bool = False) -> RText:
        url = data.get('url', '')
        file = data.get('file', '')
        summary = data.get('summary', '').strip('[]')

        image_link = url or file

        if chat_image:
            return f'[[CICode,url={image_link},name={summary}]]'

        text = f"[图片:{summary}]" if summary else "[图片]"
        result = RText(text, color=RColor.gold)
        if image_link:
            result = result.set_hover_text(image_link)\
                           .set_click_event(action=RAction.open_url, value=image_link)
        return result




