import os
import httpx
import fitz
import openpyxl

client = httpx.Client(base_url='http://127.0.0.1:8000', timeout=60.0)

# 1. Test DWG -> PDF conversion without watermark
dwg_file = 'C:/Users/musthaque.mayalankot/.gemini/antigravity/scratch/i-love-files/temp/1ca23bb8-9183-4930-a95f-8a7f643d8e53/0014t-X001-010-15.dwg'
with open(dwg_file, 'rb') as f:
    r = client.post('/api/convert', files={'file': ('drawing_clean.dwg', f, 'application/acad')}, data={'target_format': 'pdf'})
print('DWG -> PDF Status:', r.status_code, r.json().get('download_url'))
assert r.status_code == 200

# Download and inspect drawings count and color
dl_url = r.json()['download_url']
dl_res = client.get(dl_url)
doc = fitz.open(stream=dl_res.content, filetype='pdf')
drawings_count = len(doc[0].get_drawings())
print('DWG PDF Drawings count:', drawings_count)
assert drawings_count > 1000

# 2. Test Markdown with Mermaid diagram -> HTML
md_text = '# Architecture Flow\n\n```mermaid\ngraph TD;\n  A[Upload CAD] --> B(Purge Watermark);\n  B --> C[Render PDF];\n```\n'
r_md = client.post('/api/convert', files={'file': ('diagram.md', md_text.encode('utf-8'), 'text/markdown')}, data={'target_format': 'html'})
print('MD -> HTML Status:', r_md.status_code)
html_content = client.get(r_md.json()['download_url']).text
assert 'class="mermaid"' in html_content
assert 'mermaid.initialize' in html_content
print('Mermaid diagram properly embedded in HTML export: True')

# 3. Test XLSX -> MD
xlsx_path = 'test_sample.xlsx'
wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'PipingData'
ws.append(['PipeID', 'Diameter', 'Material'])
ws.append(['P-101', '6 inch', 'Carbon Steel'])
wb.save(xlsx_path)

with open(xlsx_path, 'rb') as f:
    r_xlsx = client.post('/api/convert', files={'file': ('data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}, data={'target_format': 'md'})
print('XLSX -> MD Status:', r_xlsx.status_code)
md_out = client.get(r_xlsx.json()['download_url']).text
print('MD Table Output:\n', md_out.strip())
assert '| PipeID | Diameter | Material |' in md_out

print('\nALL NEW FEATURES TESTED AND VERIFIED SUCCESSFULLY!')
