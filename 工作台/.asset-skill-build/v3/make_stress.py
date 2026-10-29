from pathlib import Path
import json
base=Path(__file__).parent
d=json.loads((base/'package/assets/blank-data.json').read_text(encoding='utf-8'))
d['meta'].update({'project':'原文压力测试（非作品）','scope':[1,1],'source_name':'自编压力样本'})
texts=['=1+1\t ▲“原文” 末尾空格  \n下一行🙂','▲长段落，保留标点和空格。'*2500]
d['source_records']=[{'id':'P001','text':texts[0],'episode':1,'scene':'1-1'},{'id':'P002','text':texts[1],'episode':1,'scene':'1-1'}]
d['assets']['角色']=[{'id':'R01','name':'测试角色','description':'只用于核对文字数据类型、空白、换行和超长段落，不属于作品。','parent_id':'','kind':'资产','source_ids':['P001','P002'],'events':[{'episode':1,'scene':'1-1','mode':'现场','source_id':'P001','inferred':False}],'candidate':False,'planned_episodes':[],'outfit_id':'','review':'不适用','user_notes':''}]
(base/'stress-data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
