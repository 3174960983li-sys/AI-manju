from pathlib import Path
import json
w=Path(__file__).parent
m=json.loads((w/'manual-manifest.json').read_text(encoding='utf-8'))
for item in m:
    old=Path(item['md']);new=old.with_name(item['title']+'.md')
    assert old.read_bytes()==Path(item['source']).read_bytes()
    assert not new.exists();old.rename(new);item['md']=str(new)
(w/'manual-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print('Same-version MD export filenames now preserve their mutual links')
