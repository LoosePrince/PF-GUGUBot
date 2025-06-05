import json
import re

from .style import get_style_template
from ..data.text import qq_face_name

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
        return f'[[CICode,url={re.sub("&amp;", "&", url)},name={summary_match}]]'
    if url_match2:
        url = url_match2.group(1)
        return f'[[CICode,url={re.sub("&amp;", "&", url)},name={summary_match}]]'
    return cq_code

def beautify_message(content:str, keep_raw_image_link:bool=False)->str:
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
        content = re.sub(r'\[CQ:image,.*?\]|\[CQ:mface,.*?\]', extract_url, content)
    else:
        content = re.sub(r'\[CQ:image,.*?\]', '[图片]', content)
        content = re.sub(r'\[CQ:mface,summary=(?:&#91;)?(.*?)(?:&#93;)?,.*?\]', r'[表情: \1]', content)

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
    if not qq_id or not qq_id.isdigit():
        return qq_id
    return f'[CQ:at,qq={qq_id}]'

def fetch_QQ_id(input_str: str, member_dict: dict) -> str:
    # is QQ id
    if input_str.isdigit():
        return input_str
    
    return str(member_dict.get(input_str, input_str))

def convert_to_CQ_at(message: str, member_dict: dict) -> str:
    pattern = r'\[@([^\s,]+)\]'
    message = re.sub(pattern, lambda m: construct_CQ_at(fetch_QQ_id(m.group(1), member_dict)), message)
    return message

