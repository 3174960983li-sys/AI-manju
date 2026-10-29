from pathlib import Path
import json,shutil,sys,hashlib
sys.stdout.reconfigure(encoding='utf-8')
SKILL=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OUT=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.1')
OUT.mkdir(parents=True,exist_ok=True)
source=json.loads(Path('.asset-skill-build/baobiao-source.json').read_text(encoding='utf-8'))
records={r['id']:r for r in source['records']}
schema=json.loads((SKILL/'assets/schema.json').read_text(encoding='utf-8'))
# Project-only enum adaptation. The reusable Skill itself is left unchanged for this test.
schema['enums']['个人或群组'].append('动物个体')
data={'meta':{'项目':'保镖驾到，大小姐爱上了我｜已有清单试跑','输入版本':'用户提供60集场景与道具精简整合清单.docx；不是逐场剧本','覆盖范围':'全文42段＋10张表；其引用的原剧60集/96分场未提供、未核验','更新日期':'2026-10-27','关键缺口':'角色/服装不完整，逐场时序、实物数量、密室身份待原剧复核。来源“原文明示”仅指本清单明示。明细序号是来源登记顺序，非剧情事件顺序。'},'sheets':{s['name']:[] for s in schema['sheets']}}
specs={s['name']:s for s in schema['sheets']}
def quote(loc):
 r=records[loc];return r.get('text','；'.join(r.get('cells',[])))
def add(sheet,loc,excerpt=None,**kw):
 s=specs[sheet];r={c:'' for c in s['columns']}
 r.update({'原文定位':f'用户精简清单 {loc}','原文摘录':(excerpt or quote(loc))[:180],'证据性质':'原文明示','确认状态':'不适用','待确认项':'需原剧分场复核，清单不能证明完整性','记录状态':'有效'})
 r.update(kw);data['sheets'][sheet].append(r);return r
def ident(sheet):return specs[sheet]['prefix']+f'-{len(data["sheets"][sheet])+1:04}'
def use(asset,loc,scope,variant='',mode='待确认',initial='未明确',end='未明确',continuity='仅清单级需求定位；无逐场出入状态证据',layer='未明确',instance=''):
 return add('出现与变化明细',loc,明细编号=ident('出现与变化明细'),集场编号='未提供分场｜'+scope,事件序号=len(data['sheets']['出现与变化明细'])+1,资产编号=asset,关联变体=variant,实例标识=instance,出现方式=mode,叙事层=layer,持有或位置='未明确',初态=initial,末态=end,交互与连续性=continuity)

roles={}
def role(name,loc,identity,scope='未明确',aliases='',typ='个人',mode='待确认',look='未明确',count='未明确'):
 if count=='未明确' and typ in ['个人','动物个体']:count=1
 k=ident('角色基础');roles[name]=k
 add('角色基础',loc,角色编号=k,名称=name,别名=aliases,个人或群组=typ,身份=identity,外观依据=look,人数=count,首次出现='清单登记：'+scope+'；首次入画未核',出现方式=mode)
 if mode!='提及':
  v=ident('角色服装与状态')
  add('角色服装与状态',loc,变体编号=v,角色编号=k,服装='未明确',妆发='未明确',年龄或形态='动物：藏獒' if typ=='动物个体' else '未明确',可见状态=look,与基准差异='待设定的基准外观；非已确认定妆',适用场次='清单范围：'+scope+'；逐场待补',制作建议='补充参考',待确认项='候选：先确定基准外观；不依据身份标签擅定服装、年龄和伤势。')
  use(k,loc,scope,v,mode)
 else:use(k,loc,scope,mode=mode)
 return k
role('江辰','T7R010','文件将“江辰孤狼”关联；主人公完整身份关系需原剧复核','第1集起',aliases='孤狼',look='半面具佩戴/摘下及通讯耳机需求；服装未明确')
role('苏小菲','T8R002','阴玉与其身体融合；耳环使用者','第1集仅玉关联，首次本人入画未明',look='耳环及棒棒糖关联；衣着妆发未明')
role('张阎王','T7R004','受伤妆造关联人物','第6集',look='受伤/毛巾/冰袋需求，伤处未明确')
role('周天','T8R008','钢铁拳套关联人物','第19集',look='钢铁拳套，其他外观未明')
role('血手','T8R009','红手套关联人物','第9集',look='标志性血红手套，左右手待核')
role('银女','T8R010','飞刀及密室修炼相关人物','首次入画未明确；飞刀第58集',look='飞刀与能量关联；“银女”不推导银发/银衣')
role('鲨鱼','P039','密室会面相关人物；姓名或称号未核','未明确',look='未明确，不按称号设计成动物')
role('神秘面具女性','P039','密室汇报相关人物；与银女关系未明','未明确',look='面具女性的指称；面具式样未明确')
role('江辰父亲','T6R011','合葬墓指向人物，不据此推定闪回演员需求','第31—32集墓地关联',mode='提及')
role('江辰母亲','T6R011','合葬墓指向人物，不据此推定闪回演员需求','第31—32集墓地关联',mode='提及')
role('大将军','T9R003','动物角色，不能归为环境道具','第3—8集别墅关联',typ='动物个体',look='藏獒；毛色、体型、性别未明')
for name in ['绑匪','打手','杀手','特工','战神卫','地下势力人员']:
 role(name,'T9R005','群众/组织关联；跨场是否同批人未明确','未明确',typ='群组',look='人数及衣着未明确；不能因组织标签生成统一制服')
role('校园背景学生','T2R003','校园环境中的群众需求，独立提取不放家具陈设','第9集起',typ='群组')
role('会所大佬群体','T5R003','两侧座席人物；与地下势力群组可能重叠，暂不误合并','第34—41集',typ='群组')
role('会所保镖群体','T5R003','会所站位人物；与其他打手群体关系未明','第34—41集',typ='群组')

def chv(name,loc,state,scope,form='未明确',cloth='未明确',advice='补充参考',base='',evidence='原文明示'):
 k=ident('角色服装与状态');row=add('角色服装与状态',loc,变体编号=k,角色编号=roles[name],基准变体编号=base,服装=cloth,妆发='未明确',年龄或形态=form,可见状态=state,与基准差异=state,适用场次=scope+'；逐场待核',制作建议=advice,证据性质=evidence)
 use(roles[name],loc,scope,k,continuity=state+'；只有需求级信息，具体起末态待原剧复核')
 return k
chv('江辰','T3R004','少年闪回外观；确切年龄与成年关联造型待核','第4集闪回',form='少年',base='CHV-0001')
chv('江辰','T8R003','孤狼银色半面具佩戴、摘下；脸型保持同一身份','第1集及后续未明确',advice='变化过程设计',base='CHV-0001')
chv('张阎王','T7R004','受伤妆造；毛巾、冰袋互动，部位程度未知','第6集',advice='补充参考',base='CHV-0003')
chv('苏小菲','T8R002','阴玉身体融合/能量表现；不表现为随手取出的玉佩','起止未明确',advice='变化过程设计',base='CHV-0002')

locs={};scene_states={}
def loc(name,parent,ref,scope,features,furniture,layout='',io='未明确',uncertain=False):
 k=ident('场景基础');locs[name]=k
 add('场景基础',ref,场景编号=k,名称=name,上级地点=parent,内外景=io,空间特征=features,家具陈设=furniture,关键布局=layout or '未明确',证据性质='合理推断' if uncertain else '原文明示',确认状态='待确认' if uncertain else '不适用',待确认项=('暂分登记避免误合并，不能断言确为不同房间；需原剧确认。' if uncertain else '清单明确的空间需求；尺寸、朝向及逐场连续性待补。'))
 v=ident('场景状态');scene_states[name]=v
 add('场景状态',ref,状态编号=v,场景编号=k,日夜与光照='未明确',天气='未明确',物理变化='基准需求；未提供完整初始物理状态',变化前后='未明确，不默认正常/完整',适用场次=scope+'；无实际分场号',制作建议='补充参考',证据性质='合理推断' if uncertain else '原文明示',确认状态='待确认' if uncertain else '不适用')
 use(k,ref,scope,v,continuity=features+'；子空间及母场景分组不等于可共用同一张图',layer='闪回' if '少年江辰' in name else '未明确')
 return k
for name,furn in [('客厅/大厅','沙发、茶几、茶具、地毯、绿植'),('餐厅','餐桌、椅、碗筷、普通食物'),('书房','未明确；不擅自添加书柜具体布局'),('卧室A','床品、枕头、柜体、灯具'),('卧室B','床品、枕头、柜体、灯具'),('走廊楼梯','未明确'),('阳台','未明确'),('院子','绿植；订婚版另记'),('大门','未明确')]:
 loc('苏家别墅·'+name,'苏家别墅｜源S01','T2R002','第3集起，高频贯穿后续','两卧室独立；阳台能看院子；具体归属未明',furn,'卧室A/B是占位标识，房间所属人物未明确；阳台视线见T5R002',io='未明确' if name in ['走廊楼梯','大门'] else '外' if name in ['阳台','院子'] else '内')
for name in ['大学门口','教学楼前','公共区','食堂']:
 loc('大学校园·'+name,'大学校园｜源S02','T2R003','第9集起；校园冲突延至22集','区位关系待核','长椅、宣传栏；食堂桌椅餐具按区域配置，学生另列角色',io='内' if name=='食堂' else '未明确')
loc('国外绑匪基地·楼顶','国外绑匪基地｜源S03','T2R004','第1集','与地面基地有俯瞰/落地关系，见T5R005','具体楼顶陈设未明确',io='外')
loc('国外绑匪基地·地面活动区','国外绑匪基地｜源S03','T2R004','第1集','含绑架位置和撤离区域；是否另室未明','烧烤架、桌椅、柱子、酒瓶、食物、杂物','与楼顶、包围方向连续；不擅定绑架区独立房间')
for name in ['外部','主要交战区域','顶楼审问区域']:
 loc('烂尾楼·'+name,'烂尾楼｜源S04','T2R005','第10—15集','与废弃工厂不同地点，不能共用同一建筑','水泥柱、钢筋、建筑废料、破损墙面；具体归区待核',io='外' if name=='外部' else '未明确')
for name in ['大门','厂房大厅']:
 loc('废弃工厂·'+name,'废弃工厂｜源S05','T2R006','第23—27集；关联段落到28集','大厅含废料堆与主打斗空地，边界待核','旧机器、工业架、废料、散落物料')
for name in ['门外','内部大厅']:
 loc('私人会所·'+name,'私人会所｜源S06','T2R007','第34—41集','中心首位、两侧座席、出入口需保持真实关系','桌椅、茶桌、主位座椅、装饰和照明','反打不能颠倒大佬与保镖左右关系',io='外' if name=='门外' else '内')
for name in ['内殿','殿外']:
 loc('裁决殿·'+name,'裁决殿｜源S07','T2R008','第42—51集','高台、台阶、两侧门为部件，非三个新房间','石柱、固定台座、座椅、灯具、纹饰','进出动线与飞身落点连续',io='内' if name=='内殿' else '外')
for name in ['室内卡座','门口采访区']:
 loc('咖啡馆·'+name,'咖啡馆｜源S08','T3R002','第2—3集','同一家店的室内/外立面对应','沙发、咖啡桌、杯具、装饰、招牌；测谎仪与采访牌独立',io='内' if name=='室内卡座' else '未明确')
loc('商场·公共通道','商场｜源S09','T3R003','第3—5集','连续公共通道；店面走廊按实际镜头扩展，不凭空增加房间','未明确')
for name in ['书房','密室']:
 loc('少年江辰的家·'+name,'少年江辰的家｜源S10','T3R004','第4集闪回','书房与密室通过墙上观察孔关联','观察孔属于空间组成；其他未明确',io='内')
loc('张阎王家·大厅','张阎王家｜源S11','T3R005','第6、9集','源“张阎王家/别墅大厅”归并在此；不与苏家别墅合并','沙发、茶几、普通茶杯',io='内')
for name in ['鲨鱼会面','面具女性汇报','银女修炼']:
 loc('反派密室·'+name+'（暂分）','反派密室｜源S12，美术模板非实体地址','P039','第22、29、53集；三者与集数对应未明确','同屋/异屋未证实；仅审美可复用','未明确',io='内',uncertain=True)
for name in ['手术室门口','病房']:
 loc('医院·'+name,'医院｜源S13','T3R007','第28—31集','两实际子空间，统一装修但不能合成一个房间','普通病床、医疗器械、走廊设施；按区域分配','推床路线与病房布局衔接',io='未明确' if name=='手术室门口' else '内')
loc('墓地·合葬墓与墓道','墓地｜源S14','T3R008','第31—32集','无名合葬墓与周边墓道固定；父母墓碑身份与无名如何对应待核','墓碑、墓道、背景植被','江辰父母合葬墓位置和特征固定；碑文原文未提供',io='外')
loc('野外空地','临时背景｜源T02','T4R003','第27—28集','审问与伏击连续戏需树木、站位和射击方向统一','树木、地形参考，细节未明确',io='外')

def lcv(name,ref,light,weather,change,scope,advice='补充参考',evidence='原文明示'):
 k=ident('场景状态');add('场景状态',ref,状态编号=k,场景编号=locs[name],基准状态编号=scene_states[name],日夜与光照=light,天气=weather,物理变化=change,变化前后='基准→'+change,适用场次=scope,制作建议=advice,证据性质=evidence)
 use(locs[name],ref,scope,k,continuity=change+'；开始/结束分场未提供')
lcv('苏家别墅·院子','T5R002','白天；具体光照未明','未明确','建筑与院子基准不变','具体集场未明确')
lcv('苏家别墅·院子','T5R002','夜间；具体光照未明','未明确','同一院子夜景，不更换建筑','具体集场未明确')
lcv('苏家别墅·院子','T6R013','未明确','未明确','叠加鲜花、迎宾与礼仪陈设；别墅不变','第53—60集关联；逐场待核')
lcv('墓地·合葬墓与墓道','T3R008','未明确','雨天','同一墓地雨天环境；雨强与地面湿润程度未明','第31—32集；具体场次未明')
lcv('张阎王家·大厅','T6R007','未明确','未明确','摔杯后普通杯破碎；碎片范围与持续待分镜','第9集关联；第22集地点不明不归入本场景',advice='变化过程设计')
for name in ['烂尾楼·主要交战区域','废弃工厂·厂房大厅']:
 lcv(name,'T6R009','未明确','未明确','候选：按原剧确认被击碎的大型部件与破损范围，不认定所有部件都破坏','具体集场未明确',advice='待判断',evidence='设计候选')
 data['sheets']['场景状态'][-1]['确认状态']='待确认'

props={}
def prop(name,ref,scope,purpose,look='未明确',state='未明确',owner='未明确',mode='待确认',count='未明确',advice='补充参考',parent=''):
 k=ident('道具需求');props[name]=k
 add('道具需求',ref,道具编号=k,名称=name,基准道具编号=parent,用途=purpose,数量=count,归属=owner,外观与文字=look,状态要求=state,适用场次=scope+'；实际分场未提供',出现方式=mode,制作建议=advice)
 use(k,ref,scope,mode=mode,continuity=state)
 return k
prop('西王母阴玉','T8R002','第1集提及，实体出现集未明','核心物件历史实物需求，身体能量不算新实体','原文未提供形制','区分历史实物与苏小菲身体融合/能量表现，不默认可取出玉佩','苏小菲关联',mode='提及',advice='独立设计')
prop('西王母阳玉','T8R002','第1集提及，实体出现集未明','与阴玉相对的核心物件','未明确','与江辰关联，是否融合及何时实体出现未明','江辰关联',mode='提及',advice='独立设计')
prop('孤狼银色半面具','T8R003','第1集','标志性佩戴物','银色、半面具','佩戴/侧面/摘下，江辰脸型不变','江辰/孤狼',advice='独立设计')
prop('昆仑琉璃灯','T8R004','第47集','核心物件','碧绿色，鸡蛋大小','实物与能量共鸣分别管理',advice='独立设计')
prop('琉璃灯配套玉盒','T8R004','第47集','容器，与琉璃灯是两件物品','玉盒，尺寸/开合未明','与灯的容纳关系待核，不和灯合成一件',advice='独立设计')
prop('裁决令','T8R005','第39集提及','身份/剧情令牌','固定符号、材质未提供具体值','与至尊令区分；实体首次出现未核',mode='提及',advice='独立设计')
true=prop('至尊令·真令','T8R006','第54集关联','真实身份令牌','未明确','真令与假令分实物实例；哪枚破碎待核',advice='独立设计')
prop('至尊令·假令','T8R006','第54集关联','仿冒令牌','真假可见差异未明','与真令是不同实物；是否同款造型待核',advice='独立设计')
prop('苏小菲耳环','T8R007','第19集','可摘戴并用于攻击的饰物','式样、尺寸未明确','耳上→摘下→手中攻击→完好→戴回；数量/左右未明','苏小菲',advice='独立设计')
prop('周天钢铁拳套','T8R008','第19集','战斗装备','钢铁，尺寸未明','完整→受击→裂纹→破裂，匹配耳环尺寸与方向','周天',advice='变化过程设计')
prop('血手红手套','T8R009','第9集','标志性装备','血红色','固定左右手与接触动作；单只/双只未明','血手',advice='独立设计')
prop('银女飞刀','T8R010','第58集','投射武器','刀型未明确','镜头数量3把/9把；黑气→金光→回射，不能直接当总数9件','银女',advice='变化过程设计')
prop('无人机','T8R011','第4集','监控设备','型号未明确','同型号悬停、飞行、监控镜头连续')
prop('测谎仪','T8R012','第2集','测试装置','指示器及连接结构未明','佩戴江辰→摘下→递还','江辰佩戴，持有者待核')
prop('烫金请柬','T8R013','第33集','关键可读文书','烫金，版式/准确文字未提供','飞入→接住→展开→阅读；文字待原剧',advice='独立设计')
prop('手机关键屏幕内容','T8R014','多集未逐条列明','屏幕内容资产，非另一台实体手机','短信/IP/威胁/情报，准确内容未提供','关联手机；各条消息应逐集拆分，不能编正文',advice='独立设计')
prop('微型计算机','T8R015','第14集','与手机连接的设备','手掌大小','接口与屏幕固定；数据线单列')
for name,ref,scope,purpose,owner in [
 ('匕首','T8R016','第6集起，具体见第6—7/24—25集','武器；普通与特写型号关系待核','未明确'),
 ('铁棍','T8R016','第6集起，具体集场待核','武器，不能与匕首/弩箭并成一种','未明确'),
 ('弩箭','T8R016','第23—28集关联，首次未明确','投射武器；数量未明确','未明确'),
 ('棒棒糖','T7R002','第2、3、9集等','人物习惯物件；次数不等于件数','苏小菲'),
 ('购物袋','T7R003','第6集','携带物；锁定连续段数量与手持位置','江辰'),
 ('毛巾','T7R004','第6集','受伤护理互动','张阎王关联'),
 ('冰袋','T7R004','第6集','受伤护理互动','张阎王关联'),
 ('玫瑰花束','T7R006','第16—17集','表白物件；跨镜同束','未明确'),
 ('水桶','T7R007','第13集','泼水互动','未明确'),
 ('雨伞','T7R008','第31—32集','墓地人物携带','未明确'),
 ('祭扫鲜花','T7R008','第31—32集','墓地人物携带；不与表白花束合并','未明确'),
 ('普通手机','T7R009','多集，未逐条列明','实体终端；屏幕内容另项关联','各人机型/实例未明'),
 ('数据线','T7R009','第14集','连接手机与微型计算机','未明确'),
 ('通讯耳机','T7R010','第1集起','佩戴配件','江辰/孤狼'),
 ('硬币','T7R012','第4集起多次','弹射物，统一动作不逐枚建设计','未明确'),
 ('石子','T7R012','第4集起多次','弹射物，与硬币分材质','未明确'),
 ('工作文件','T7R013','多集','普通文书；准确文字需求时另补内容','未明确'),
 ('书稿','T7R013','多集','稿件；不因普通文件相近而误合并','未明确'),
 ('寻找路人英雄广告牌','T10R003','第2—3集','采访展示物，非咖啡馆固定家具','未明确'),
 ('绑缚绳索','T6R002','第1集','挣扎/解救特写按实际镜头锁定','绑架关系未明')]:
 prop(name,ref,scope,purpose,owner=owner,look='已知文案片段：“寻找路人英雄”；全版文案未提供' if '广告牌' in name else '未明确',state='按原剧/镜头补充；不因临时生成而省略需求登记')

# All original rows are covered by an explicit source map, including policy-only prose.
coverage=[]
for r in source['records']:
 key=r['id'];text=r.get('text','；'.join(r.get('cells',[])))
 targets=[]
 for sheet,rows in data['sheets'].items():
  for row in rows:
   if row['原文定位'].endswith(' '+key):targets.append(row[specs[sheet]['key']])
 coverage.append({'来源定位':key,'内容':text,'关联编号':targets,'处理': '已关联需求记录' if targets else ('表头/结构/空段' if not text or (key.startswith('T') and key.endswith('001')) else '已阅读，作为制作建议/复核约束；不自动据此新增身份或实体')})
supplement=[
 {'类别':'交通资产','名称':'直升机','范围':'第1集','要求':'统一机身、座舱、舱门方向；实际型号/数量未明确','来源':'T4R002/T9R004/T10R002'},
 {'类别':'交通资产','名称':'保姆车','范围':'第3集','要求':'车内外、座椅、车门匹配；不与豪车合并','来源':'T4R002/T9R004'},
 {'类别':'交通资产','名称':'豪车','范围':'第9集起','要求':'具体车种、车辆数量、归属待原剧；不能只建一个通用实例','来源':'T4R002/T9R004'},
]
for name in ['高速闪现','拳脚冲击','伤口自愈','绿色治疗','金银能量','黑气','飞刀悬浮与回射','残魂消散','西王母玉身体融合与共鸣','琉璃灯能量共鸣','爆炸']:
 supplement.append({'类别':'特效需求','名称':name,'范围':'起止集场未明确，待原剧','要求':'绑定具体人物/物件、起末态与剧情阶段；不是新增实体道具','来源':'T9R002/T8R002/T8R004/T8R010/T10R002'})
(OUT/'资产拆解中间数据.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'来源逐项覆盖.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'专项需求.json').write_text(json.dumps(supplement,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'来源定位与原文抽取.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
scratch=Path('.asset-skill-build/baobiao-package');shutil.copytree(SKILL,scratch,dirs_exist_ok=True)
(scratch/'assets/schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
# Tailor only the trial builder's overview: retain seven sheets, show out-of-schema requirements without counting them as props.
builder=(scratch/'scripts/build_workbook.mjs').read_text(encoding='utf-8')
builder=builder.replace("const notes=[", "const notes=[")
builder=builder.replace("sheet.tables.add(`A4:${end}${last}`,true,'Assets'+spec.prefix)","sheet.tables.add(`A4:${end}${last}`,true,'Assets'+spec.prefix)")
height="""
 for(const [ri,record]of rows.entries()){
  let maxLines=1;
  for(const [ci,key]of spec.columns.entries()){
   const broad=['原文摘录','待确认项','变更说明','用户批注','交互与连续性','可见状态','物理变化','家具陈设','外观与文字','服装','关键布局','变化前后','与基准差异','外观依据','身份'].includes(key);
   const width=broad?32:ci<2?18:22;
   const text=String(record[key]??'');const units=[...text].reduce((n,c)=>n+(c.charCodeAt(0)>255?2:1),0);
   maxLines=Math.max(maxLines,Math.ceil(units/Math.max(12,width-2)));
  }
  sheet.getRange(`A${ri+5}:${end}${ri+5}`).format.rowHeight=Math.max(48,maxLines*15+10);
 }
"""
builder=builder.replace("const table=sheet.tables.add",height+"\n const table=sheet.tables.add")
builder=builder.replace("['当前状态','合成小样待审。清单描述需求，不代表素材已制作或绑定。']", "['当前状态','实际清单试跑待审；非原剧全文提取，实际入画与角色完整性未验证。']")
marker='wb.recalculate();'
block="""
const special=JSON.parse(await fs.readFile(path.join(outdir,'专项需求.json'),'utf8'));
overview.getRange('A27').values=[['交通与特效专项需求（不计入普通道具）']];
overview.getRange('A29:F29').values=[['类别','名称','范围','要求','来源','核验状态']];
overview.getRange('A29:F29').format={fill:'#304B6A',font:{bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:32};
overview.getRange('C29:C50').format.columnWidth=34;
overview.getRange('D29:D50').format.columnWidth=55;
overview.getRange('E29:F50').format.columnWidth=24;
overview.getRange('A30:F'+(special.length+29)).values=special.map(r=>[r['类别'],r['名称'],r['范围'],r['要求'],r['来源'],'需求待原剧复核']);
overview.getRange('A30:F'+(special.length+29)).format.wrapText=true;
overview.getRange('A30:F'+(special.length+29)).format.rowHeight=58;
overview.getRange('A26').values=[['明细读取提醒']];overview.getRange('B26').values=[['明细列“集场编号”是源清单集数范围，不是96分场；事件序号只用于登记排序。']];
overview.getRange('B26').format.wrapText=true;overview.getRange('A26:B26').format.rowHeight=45;
"""
builder=builder.replace(marker,block+'\n'+marker)
(scratch/'scripts/build_workbook.mjs').write_text(builder,encoding='utf-8')
sys.path.insert(0,str(scratch/'scripts'))
from check_data import check
errors=check(data,schema)
if errors:raise RuntimeError(errors)
print(json.dumps({'output':str(OUT),'counts':{k:len(v) for k,v in data['sheets'].items()},'source_records':len(coverage),'supplement':len(supplement)},ensure_ascii=False))
