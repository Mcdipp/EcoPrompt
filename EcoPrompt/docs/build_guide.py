"""Convertit guide_demonstration.md en PDF (même identité visuelle jaune que le rapport)."""
import asyncio
from pathlib import Path

import markdown
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
md = (HERE / "guide_demonstration.md").read_text(encoding="utf-8")
md = md.replace("- [ ]", "- ☐")
body = markdown.markdown(md, extensions=["tables"])
html = f"""<!doctype html><html lang="fr"><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm 20mm; }}
body {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 10.2pt; line-height: 1.45; color:#111; }}
h1 {{ background:#FFE11F; padding:14px 16px; margin:0 0 12px; font-size:19pt; }}
h2 {{ font-size:13pt; border-bottom:3px solid #FFE11F; padding-bottom:2px; margin-top:16px; }}
h3 {{ font-size:11pt; margin:12px 0 4px; }}
table {{ border-collapse:collapse; width:100%; font-size:9pt; margin:6px 0 10px; }}
th {{ background:#FFE11F; text-align:left; }} th,td {{ border:1px solid #ccc; padding:4px 6px; vertical-align:top; }}
blockquote {{ margin:6px 0; padding:6px 12px; background:#FFF8D6; border-left:4px solid #FFD200; font-style:italic; }}
code {{ background:#F3F3F3; padding:0 3px; }} ul {{ margin:4px 0; }}
tr, blockquote {{ page-break-inside: avoid; }}
</style><body>{body}</body></html>"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.set_content(html)
        await pg.pdf(path=str(HERE / "EcoPrompt_Guide_Demonstration.pdf"), format="A4",
                     print_background=True, margin={"top": "18mm", "bottom": "18mm",
                                                    "left": "20mm", "right": "20mm"})
        await b.close()

asyncio.run(main())
print("Guide généré.")
