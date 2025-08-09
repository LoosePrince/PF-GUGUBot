import json
import re

from mcdreforged.api.rtext import RText, RAction, RColor

from gugubot.utils.style import get_style_template
from gugubot.data.text import qq_face_name

def replace_emoji(match):
    emoji_id = match.group(1)
    emoji_display = qq_face_name.get(str(emoji_id))
    return f'[表情: {emoji_display}]' if emoji_display else '[表情]'

def process_json(match):
    json_data = match.group(1).replace('&#44;', ',').replace('&#91;', '[').replace('&#93;', ']')
    parsed_data = json.loads(json_data)
    desc = parsed_data.get('meta', {}).get('detail_1', {}).get('desc', '')
    group_notice = parsed_data.get('prompt', '')
    return ('[链接]' + desc) if desc else group_notice if group_notice else ''

def extract_url(match):
    cq_code = match.group(0)
    pattern = r'url=([^\s,\]]+)'
    pattern2 = r'file=([^\s,\]]+)'
    summary_pattern = r'summary=(?:&#91;)?(.*?)(?:&#93;)?,'
    url_match = re.search(pattern, cq_code)
    url_match2 = re.search(pattern2, cq_code)
    summary_match = re.search(summary_pattern, cq_code)
    summary_match = f"表情: {summary_match.group(1)}" if summary_match else '图片'
    if url_match:
        url = url_match.group(1)
        return url, summary_match
    if url_match2:
        url = url_match2.group(1)
        return url, summary_match
    return cq_code

def construct_ChatImage_url(url, summary="图片"):
    return f'[[CICode,url={re.sub("&amp;", "&", url)},name={summary}]]'

def construct_Image_url(url, summary="图片"):
    return f'[图片: {summary}]({re.sub("&amp;", "&", url)})'

def replace_emoji_with_placeholder(text):
    # 定义匹配 emoji 的正则表达式
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # 表情符号
        "\U0001F300-\U0001F5FF"  # 各种符号和图标
        "\U0001F680-\U0001F6FF"  # 交通工具和符号
        "\U0001F700-\U0001F77F"  # 阿尔化学符号
        "\U0001F780-\U0001F7FF"  # 几何图形
        "\U0001F800-\U0001F8FF"  # 补充箭头
        "\U0001F900-\U0001F9FF"  # 补充表情
        "\U0001FA00-\U0001FA6F"  # 补充工具和物品
        "\U0001FA70-\U0001FAFF"  # 补充文化符号
        "\u2600-\u26FF"          # 杂项符号
        "\u2700-\u27BF"          # Dingbats
        "]+", flags=re.UNICODE
    )
    # 替换 emoji 为 `[emoji]`
    return emoji_pattern.sub("[emoji]", text)

def beautify_message(content:str, keep_raw_image_link:bool=False, low_game_version:bool=False)->str:
    content = re.sub(r'\[CQ:record,file=.*?\]', '[语音]', content)
    content = re.sub(r'\[CQ:video,file=.*?\]', '[视频]', content)
    content = re.sub(r'\[CQ:rps\]', '[猜拳]', content)
    content = re.sub(r'\[CQ:dice\]', '[掷骰子]', content)
    content = re.sub(r'\[CQ:shake\]', '[窗口抖动]', content)
    content = re.sub(r'\[CQ:poke,.*?\]', "[戳一戳]", content)
    content = re.sub(r'\[CQ:anonymous.*?\]', "[匿名消息]", content)
    content = re.sub(r'\[CQ:share,file=.*?\]', '[链接]', content)
    content = re.sub(r'\[CQ:contact,type=qq.*?\]', "[推荐好友]", content)
    content = re.sub(r'\[CQ:contact,type=group.*?\]', "[推荐群]", content)
    content = re.sub(r'\[CQ:location,.*?\]', "[推荐群]", content)
    content = re.sub(r'\[CQ:music,type=.*?\]', '[音乐]', content)
    content = re.sub(r'\[CQ:forward,id=.*?\]', '[转发消息]', content)
    content = re.sub(r'\[CQ:xml(?:,.*?)*\]', '', content)
    content = re.sub(r'\[CQ:file(?:,.*?)*\]', '[文件]', content)
    content = re.sub(r'\[CQ:redbag,title=.*?\]', '[红包]', content)
    content = re.sub(r'\[CQ:markdown,content=.*?\]', '', content)
    
    content = re.sub(r'\[CQ:at,qq=(\d+)(?:,.*?)*\]', r'[@\1]', content)

    # process emoji
    content = re.sub(r'\[CQ:face,id=(\d+?)(?:,.*?)*\]', replace_emoji, content)

    # process json
    content = re.sub(r'\[CQ:json,.*?data=(\{[^,]*\}).*?\s*\]', process_json, content)

    # process image link
    if keep_raw_image_link:
        content = re.sub(r'\[CQ:image,.*?\]|\[CQ:mface,.*?\]', \
                         lambda x: construct_ChatImage_url(*extract_url(x)), content)
    else:
        content = re.sub(r'\[CQ:image,.*?\]|\[CQ:mface,.*?\]', \
                         lambda x: construct_Image_url(*extract_url(x)), content)

    # process emoji
    if low_game_version:
        content = replace_emoji_with_placeholder(content)

    return content



def format_list_response(player_list, bot_list, player_status, server_status, style):
        respond = ""
        count = 0

        if player_status or server_status:
            respond += format_player_list(player_list, style)
            count += len(player_list)

        if not player_status:
            respond += format_bot_list(bot_list)
            count += len(bot_list)

        if count != 0:
            respond = get_style_template('player_list', style).format(
                count,
                '玩家' if player_status else '假人' if not server_status else '人员',
                '\n' + respond
            )
        elif count == 0:
            respond = get_style_template('no_player_ingame', style)

        return respond

def format_player_list(player_list, style):
    if player_list:
        return f"\n---玩家---\n" + '\n'.join(sorted(player_list))
    return get_style_template('no_player_ingame', style)

def format_bot_list(bot_list):
    if bot_list:
        return f"\n\n---假人---\n" + '\n'.join(sorted(bot_list))
    return '\n\n没有假人在线哦!'

def construct_CQ_at(qq_id: str) -> str:
    if qq_id and qq_id.isdigit():  
        return f'[CQ:at,qq={qq_id}]'
    return qq_id

def fetch_QQ_id(input_str: str, member_dict: dict) -> str:
    # is QQ id
    if input_str.isdigit():
        return input_str
    
    return str(member_dict.get(input_str, input_str))

def convert_to_CQ_at(message: str, member_dict: dict) -> str:
    pattern = r'\[@([^\s,]+)\]'
    message = re.sub(pattern, lambda m: construct_CQ_at(fetch_QQ_id(m.group(1), member_dict)), message)
    return message

def convert_message_to_RText(message: str, use_image_preview:bool=False) -> RText:
    image_pattern = re.compile(r'\[图片: (.*?)\]\((.*?)\)')

    def replace_image(match):
        summary = match.group(1)
        image_summary = f'[图片: {summary}]' if summary!="图片" else '[图片]'
        url = match.group(2)

        if use_image_preview:
            return RText(image_summary, color=RColor.gold) \
            .set_hover_text(url) \
            .set_click_event(action=RAction.run_command, value=f"/imagepreview preview {url} 60")

        return RText(image_summary, color=RColor.gold) \
            .set_hover_text(url) \
            .set_click_event(action=RAction.open_url, value=url)

    last_end = 0
    result = RText('', color=RColor.white)
    for match in image_pattern.finditer(message):
        if match.start() > last_end:
            result += RText(message[last_end:match.start()], color=RColor.white)
        result += replace_image(match)
        last_end = match.end()
    if last_end < len(message):
        result += RText(message[last_end:], color=RColor.white)
    return result

