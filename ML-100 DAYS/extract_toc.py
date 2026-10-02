import fitz
import json
import os
import re

def extract_toc():
    pdf_path = "100 days ML Notes v2.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    doc = fitz.open(pdf_path)
    raw_toc = doc.get_toc()
    print(f"Total raw TOC entries: {len(raw_toc)}")

    chapters = []
    curr_ch = None
    curr_sec = None

    # Track chapter start pages for reverse lookup
    chapter_lookup = []

    for lvl, title, page in raw_toc:
        clean_title = re.sub(r'\s+', ' ', title).strip()
        
        if lvl == 1:
            curr_ch = {
                'id': len(chapters) + 1,
                'title': clean_title,
                'page': page,
                'sections': []
            }
            chapters.append(curr_ch)
            curr_sec = None
            chapter_lookup.append({
                'id': curr_ch['id'],
                'title': clean_title,
                'page': page
            })
        elif lvl == 2:
            if curr_ch is None:
                curr_ch = {
                    'id': 1,
                    'title': 'Introduction',
                    'page': page,
                    'sections': []
                }
                chapters.append(curr_ch)
                chapter_lookup.append({
                    'id': 1,
                    'title': 'Introduction',
                    'page': page
                })
            curr_sec = {
                'title': clean_title,
                'page': page,
                'subsections': []
            }
            curr_ch['sections'].append(curr_sec)
        elif lvl == 3:
            if curr_sec is None:
                if curr_ch is None:
                    curr_ch = {
                        'id': 1,
                        'title': 'Introduction',
                        'page': page,
                        'sections': []
                    }
                    chapters.append(curr_ch)
                    chapter_lookup.append({
                        'id': 1,
                        'title': 'Introduction',
                        'page': page
                    })
                curr_sec = {
                    'title': 'General',
                    'page': page,
                    'subsections': []
                }
                curr_ch['sections'].append(curr_sec)
            curr_sec['subsections'].append({
                'title': clean_title,
                'page': page
            })

    # Also build a flat search index for instant filtering
    flat_items = []
    for ch in chapters:
        flat_items.append({
            'type': 'chapter',
            'title': ch['title'],
            'page': ch['page'],
            'chapterId': ch['id'],
            'chapterTitle': ch['title']
        })
        for sec in ch['sections']:
            flat_items.append({
                'type': 'section',
                'title': sec['title'],
                'page': sec['page'],
                'chapterId': ch['id'],
                'chapterTitle': ch['title']
            })
            for sub in sec['subsections']:
                flat_items.append({
                    'type': 'subsection',
                    'title': sub['title'],
                    'page': sub['page'],
                    'chapterId': ch['id'],
                    'chapterTitle': ch['title'],
                    'sectionTitle': sec['title']
                })

    js_content = f"""// Auto-generated from 100 days ML Notes v2.pdf
const TOTAL_PAGES = {len(doc)};
const TOC_DATA = {json.dumps(chapters, ensure_ascii=False, indent=2)};
const CHAPTER_LOOKUP = {json.dumps(chapter_lookup, ensure_ascii=False, indent=2)};
const TOC_FLAT = {json.dumps(flat_items, ensure_ascii=False)};
"""

    with open("toc_data.js", "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Successfully generated toc_data.js:")
    print(f"  - Total Pages: {len(doc)}")
    print(f"  - Chapters: {len(chapters)}")
    print(f"  - Flat Search Items: {len(flat_items)}")

if __name__ == "__main__":
    extract_toc()
