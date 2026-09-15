import io,re,sys
h=io.open('office-3d-taskboard.html',encoding='utf-8').read()
ms=re.findall(r'<script type="module">(.*?)</script>',h,re.S)
print("module script blocks:",len(ms))
io.open('_verify/_check.mjs','w',encoding='utf-8').write(ms[-1])
