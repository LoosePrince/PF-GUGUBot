from .data.text import style, qq_face_name
from .table import table

import json
import os
import re

def get_style()->dict:
    config = table("./config/GUGUbot/config.json", yaml=True)
    extra_style = read_extra_style(config['dict_address'].get('extra_style_path', ""))
    style.update(extra_style)
    return style

def read_extra_style(extra_style_path)->dict:
    if os.path.exists(extra_style_path):
        with open(extra_style_path, 'r', encoding='UTF-8') as f:
            extra_style = json.load(f)
        return extra_style
    return {}

def get_style_template(template_name:str, current_style:str)->str:
    style = get_style()
    style_template = style[current_style].get(template_name, None)
    normal_template = style['正常'][template_name]

    if style_template is not None \
        and style_template.count("{}") == normal_template.count("{}"):
        return style_template
    return normal_template

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

def replace_emoji(match):
    emoji_id = match.group(1)
    emoji_display = qq_face_name.get(str(emoji_id))
    return f'[表情: {emoji_display}]' if emoji_display else '[表情]'

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
    content = re.sub(r'\[CQ:file(?:,.*?)*\]', '[文件]', content)
    content = re.sub(r'\[CQ:redbag,title=.*?\]', '[红包]', content)
    content = re.sub(r'\[CQ:markdown,content=.*?\]', '', content)
    
    content = content.replace('CQ:at,qq=', '@')

    # process emoji
    content = re.sub(r'\[CQ:face,id=(\d+?)\]', replace_emoji, content)

    # process json
    content = re.sub(r'\[CQ:json,.*?data=(\{[^,]*\}).*?\s*\]', process_json, content)

    # process image link
    if keep_raw_image_link:
        content = re.sub(r'\[CQ:image,.*?\]|\[CQ:mface,.*?\]', extract_url, content)
    else:
        content = re.sub(r'\[CQ:image,file=.*?\]', '[图片]', content)
        content = re.sub(r'\[CQ:mface,summary=(?:&#91;)?(.*?)(?:&#93;)?,.*?\]', r'[表情: \1]', content)

    return content

    