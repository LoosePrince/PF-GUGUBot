# -*- coding: utf-8 -*-
import json
import os
import yaml
from pathlib import Path
class table(object):    

    def __init__(self,path:str="./default.json", default_content:dict=None, yaml:bool=False) -> None: # 初始化，记录系统路径
        self.yaml = yaml
        self.path = path if not self.yaml else path.replace(".json", ".yml")
        self.path = Path(self.path)
        self.default_content = default_content
        self.load()    

    def load(self) -> None: # 读取
        if os.path.isfile(self.path) and os.path.getsize(self.path) != 0:
            with open(self.path, 'r', encoding='UTF-8') as f:
                if self.yaml:
                    self.data = yaml.load(f, Loader=yaml.FullLoader)
                else:
                    self.data = json.load(f)
        else:
            self.data = self.default_content if self.default_content else {}
            self.save()

    def save(self) -> None: # 储存
        self.path.parents[0].mkdir(parents=True, exist_ok=True)
        if self.yaml:
            with open(self.path, 'w', encoding='UTF-8') as f:
                yaml.dump(self.data, f, allow_unicode=True)        
        else:
            with open(self.path, 'w', encoding='UTF-8') as f:
                json.dump(self.data, f, ensure_ascii= False)        
    
    def __getitem__(self, key:str): # 获取储存内容
        return self.data[key]    

    def __setitem__(self, key:str, value): # 增加，修改
        self.data[key] = value
        self.save()   

    def __contains__(self,key:str): # in 
        return key in self.data

    def __delitem__(self,key:str): # 删除
        if key in self.data:
            del self.data[key]
            self.save()

    def __iter__(self):
        return iter(self.data.keys())

    def __repr__(self) -> str: # 打印
        if self.data is None:
            return ""
        return str(self.data)

    def __len__(self):
        return len(self.data)

    def get(self, key:str, default=None):
        return self.data.get(key, default)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

if __name__ == "__main__":
    # test __init__
    test_table = table()
    # test keys, del
    for k in [i for i in test_table.keys()]:
        del test_table[k]
    assert len(test_table) == 0, 'Error on keys or del'
    # test adding
    test_table['key'] = 'value'
    test_table['钥匙'] = '值'
    assert test_table['key'] == 'value' , 'Error on __setitem__'
    assert test_table['钥匙'] == '值', 'Error on __setitem__'
    # test items
    assert test_table.items() == test_table.data.items()
    # test del
    del test_table['key']
    assert test_table.data.get('key', None) is None
    # test contain
    assert '钥匙' in test_table, 'Error in __contain__'
    


