from .data.text import style
from .table import table
import json
import os

def get_style()->dict:
    config = table("./config/GUGUBot/config.json", yaml=True)
    extra_style = read_extra_style(config['dict_address'].get('extra_style_path', ""))
    style.update(extra_style)
    return style

def read_extra_style(extra_style_path)->dict:
    if os.path.exists(extra_style_path):
        with open(extra_style_path, 'r', encoding='UTF-8') as f:
            extra_style = json.load(f)
        return extra_style
    return {}

style = get_style()

def get_style_template(template_name:str, current_style:str)->str:
    style_template = style[current_style].get(template_name, None)
    normal_template = style['正常'][template_name]

    if style_template is not None \
        and style_template.count("{}") == normal_template.count("{}"):
        return style_template
    return normal_template


              
    