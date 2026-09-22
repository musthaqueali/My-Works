import fitz
doc = fitz.open('test_dwg_final.pdf')
drawings = doc[0].get_drawings()
for i, d in enumerate(drawings):
    r = d['rect']
    area = r.width * r.height
    if area > 1000 and d.get('fill') != (0.12941177189350128, 0.1568627506494522, 0.1882352977991104):
        print(f"Drawing {i}: Type={d['type']}, Layer={d.get('layer')}, Fill={d.get('fill')}, Color={d.get('color')}, Width={d.get('width')}, Rect={r}")
