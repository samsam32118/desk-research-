#!/usr/bin/env python3
"""Turn the scan (and your analysis) into an Excel workbook.

Six sheets, each answering a different question:
  Companies  — one row per company: who they are, how they position, what they charge
  Pages      — one row per page: the meta title/description and heading ladder
  Headings   — one row per heading, so you can pivot on language
  Matrices   — every company's coordinates on every 2x2, with the evidence
  Vocabulary — which words the market shares (table stakes) vs. owns (differentiation)
  Sources    — the URLs the analysis leaned on

Writes a real .xlsx with the standard library only -- no openpyxl, no pandas,
so it runs anywhere.

Usage:
    python3 build_workbook.py --data data/ --out blixon-landscape.xlsx
    python3 build_workbook.py --data data/ --analysis analysis.json --out out.xlsx
"""

import argparse
import glob
import json
import os
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone

ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def esc(text):
    text = ILLEGAL.sub("", str(text))
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def col_letter(idx):
    name = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        name = chr(65 + rem) + name
    return name


class MiniXlsx:
    """The smallest xlsx that Excel, Numbers, LibreOffice and Sheets all open."""

    def __init__(self):
        self.sheets = []

    def add(self, name, headers, rows, widths=None):
        clean = re.sub(r"[\[\]:*?/\\]", "-", str(name))[:31] or "Sheet"
        self.sheets.append((clean, headers, rows, widths or []))

    def _sheet_xml(self, headers, rows, widths):
        ncols = max([len(headers)] + [len(r) for r in rows]) if headers or rows else 1
        dim = "A1:%s%d" % (col_letter(max(1, ncols)), len(rows) + 1)
        cols = "".join(
            '<col min="%d" max="%d" width="%d" customWidth="1"/>' % (i + 1, i + 1, w)
            for i, w in enumerate(widths[:ncols]) if w)
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
               '<dimension ref="%s"/>' % dim,
               '<sheetViews><sheetView workbookViewId="0">'
               '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
               '</sheetView></sheetViews>',
               '<sheetFormatPr defaultRowHeight="15"/>']
        if cols:
            out.append("<cols>%s</cols>" % cols)
        out.append("<sheetData>")
        cells = "".join(
            '<c r="%s1" s="1" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
            % (col_letter(i + 1), esc(h)) for i, h in enumerate(headers))
        out.append('<row r="1" ht="18" customHeight="1">%s</row>' % cells)
        for r, row in enumerate(rows, start=2):
            cells = []
            for c, value in enumerate(row):
                ref = "%s%d" % (col_letter(c + 1), r)
                if isinstance(value, bool) or value is None or value == "":
                    continue
                if isinstance(value, (int, float)):
                    cells.append('<c r="%s"><v>%s</v></c>' % (ref, value))
                else:
                    text = str(value)[:32000]
                    cells.append('<c r="%s" s="2" t="inlineStr"><is><t xml:space="preserve">%s</t>'
                                 "</is></c>" % (ref, esc(text)))
            out.append('<row r="%d">%s</row>' % (r, "".join(cells)))
        out.append("</sheetData>")
        if rows:
            out.append('<autoFilter ref="%s"/>' % dim)
        out.append("</worksheet>")
        return "".join(out)

    def save(self, path):
        n = len(self.sheets)
        types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                 '<Default Extension="xml" ContentType="application/xml"/>',
                 '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
                 'officedocument.spreadsheetml.sheet.main+xml"/>',
                 '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-'
                 'officedocument.spreadsheetml.styles+xml"/>']
        for i in range(1, n + 1):
            types.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType='
                         '"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % i)
        types.append("</Types>")

        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>']

        wb = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
        for i, (name, _, _, _) in enumerate(self.sheets, start=1):
            wb.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (esc(name), i, i))
        wb.append("</sheets></workbook>")

        wbrels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
        for i in range(1, n + 1):
            wbrels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/'
                          '2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i, i))
        wbrels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/'
                      '2006/relationships/styles" Target="styles.xml"/></Relationships>' % (n + 1))

        styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                  '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
                  '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
                  '<fills count="3"><fill><patternFill patternType="none"/></fill>'
                  '<fill><patternFill patternType="gray125"/></fill>'
                  '<fill><patternFill patternType="solid"><fgColor rgb="FF1F3B57"/>'
                  '<bgColor indexed="64"/></patternFill></fill></fills>'
                  '<borders count="1"><border/></borders>'
                  '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                  '<cellXfs count="3">'
                  '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                  '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" '
                  'applyFill="1" applyAlignment="1"><alignment vertical="center"/></xf>'
                  '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
                  '<alignment vertical="top" wrapText="1"/></xf></cellXfs>'
                  '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                  "</styleSheet>")

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", "".join(types))
            z.writestr("_rels/.rels", "".join(rels))
            z.writestr("xl/workbook.xml", "".join(wb))
            z.writestr("xl/_rels/workbook.xml.rels", "".join(wbrels))
            z.writestr("xl/styles.xml", styles)
            for i, (_, headers, rows, widths) in enumerate(self.sheets, start=1):
                z.writestr("xl/worksheets/sheet%d.xml" % i, self._sheet_xml(headers, rows, widths))
        return path


# --------------------------------------------------------------------------- data

def load_scans(data_dir):
    sites = {}
    for path in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        if os.path.basename(path) in ("roster.json", "analysis.json"):
            continue
        with open(path, encoding="utf-8") as fh:
            site = json.load(fh)
        sites[site["domain"]] = site
    return sites


def join(values, sep=" | ", limit=12):
    return sep.join(v for v in (values or [])[:limit])


def quadrant(x, y):
    return ("%s-%s" % ("top" if y >= 5 else "bottom", "right" if x >= 5 else "left"))


def build(data_dir, analysis, out_path):
    sites = load_scans(data_dir)
    profiles = {c.get("domain", ""): c for c in analysis.get("companies", [])}
    order = {d: i for i, d in enumerate(profiles)}
    book = MiniXlsx()

    # -- Companies ---------------------------------------------------------
    headers = ["level", "name", "domain", "category", "segment", "geo", "discovered_via",
               "parent", "one_liner", "positioning", "icp", "pricing_model", "price_signal",
               "key_claims", "homepage_title", "homepage_meta_description", "homepage_h1",
               "ctas", "pages_scanned", "headings_found", "scan_notes"]
    rows = []
    for domain in sorted(set(sites) | set(profiles),
                         key=lambda d: (profiles.get(d, {}).get("level", 9), order.get(d, 999), d)):
        site, prof = sites.get(domain, {}), profiles.get(domain, {})
        pages = site.get("pages", [])
        home = next((p for p in pages if p["page_type"] == "home"), pages[0] if pages else {})
        rows.append([
            prof.get("level", ""), prof.get("name") or site.get("name") or domain, domain,
            prof.get("category", ""), prof.get("segment", ""), prof.get("hq") or prof.get("geo", ""),
            prof.get("discovered_via", ""), prof.get("parent", ""), prof.get("one_liner", ""),
            prof.get("positioning", ""), prof.get("icp", ""), prof.get("pricing_model", ""),
            prof.get("price_signal", ""), join(prof.get("key_claims"), "; "),
            home.get("title", ""), home.get("meta_description", ""), join(home.get("h1"), " / ", 3),
            join(home.get("ctas"), ", ", 5), len(pages), site.get("headings_found", 0),
            join(site.get("notes"), "; ", 4),
        ])
    book.add("Companies", headers, rows,
             [6, 22, 24, 20, 14, 10, 30, 16, 46, 46, 30, 22, 18, 46, 42, 52, 42, 22, 8, 8, 40])

    # -- Pages -------------------------------------------------------------
    headers = ["company", "domain", "level", "page_type", "url", "status", "meta_title",
               "meta_description", "h1", "h2", "h3", "ctas", "word_count"]
    rows = []
    for domain, site in sites.items():
        prof = profiles.get(domain, {})
        for page in site.get("pages", []):
            rows.append([prof.get("name") or site.get("name") or domain, domain,
                         prof.get("level", ""), page["page_type"], page["final_url"], page["status"],
                         page["title"], page["meta_description"], join(page["h1"], " / ", 3),
                         join(page["h2"], " | ", 20), join(page["h3"], " | ", 25),
                         join(page["ctas"], ", ", 5), page["word_count"]])
    book.add("Pages", headers, rows, [22, 22, 6, 12, 46, 7, 42, 52, 40, 70, 60, 20, 9])

    # -- Headings (long format, for pivots) --------------------------------
    headers = ["company", "domain", "level", "page_type", "url", "tag", "position", "text"]
    rows = []
    for domain, site in sites.items():
        prof = profiles.get(domain, {})
        name = prof.get("name") or site.get("name") or domain
        for page in site.get("pages", []):
            for tag in ("h1", "h2", "h3"):
                for i, text in enumerate(page.get(tag, []), start=1):
                    rows.append([name, domain, prof.get("level", ""), page["page_type"],
                                 page["final_url"], tag, i, text])
    book.add("Headings", headers, rows, [22, 22, 6, 12, 44, 5, 8, 90])

    # -- Matrices ----------------------------------------------------------
    headers = ["matrix_id", "matrix_title", "x_axis", "x_low", "x_high", "y_axis", "y_low",
               "y_high", "company", "domain", "level", "x", "y", "quadrant", "quadrant_label",
               "evidence"]
    rows = []
    for m in analysis.get("matrices", []):
        x, y = m.get("x", {}), m.get("y", {})
        quads = m.get("quadrants", {})
        key = {"top-right": "tr", "top-left": "tl", "bottom-right": "br", "bottom-left": "bl"}
        for pt in m.get("points", []):
            prof = profiles.get(pt.get("domain", ""), {})
            if not prof:
                prof = next((c for c in analysis.get("companies", [])
                             if c.get("id") == pt.get("company")), {})
            q = quadrant(pt.get("x", 5), pt.get("y", 5))
            rows.append([m.get("id", ""), m.get("title", ""), x.get("label", ""), x.get("low", ""),
                         x.get("high", ""), y.get("label", ""), y.get("low", ""), y.get("high", ""),
                         prof.get("name") or pt.get("company", ""), prof.get("domain", ""),
                         prof.get("level", ""), pt.get("x"), pt.get("y"), q,
                         quads.get(key[q], ""), pt.get("evidence", "")])
    book.add("Matrices", headers, rows, [16, 40, 24, 24, 24, 24, 24, 24, 22, 22, 6, 6, 6, 12, 24, 70])

    # -- Vocabulary --------------------------------------------------------
    from digest import STOPWORDS
    doc_freq, total = Counter(), Counter()
    for site in sites.values():
        seen = set()
        for page in site.get("pages", []):
            blob = " ".join([page["title"], page["meta_description"]]
                            + page["h1"] + page["h2"] + page["h3"])
            for w in re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", blob.lower()):
                if w in STOPWORDS or len(w) < 3:
                    continue
                total[w] += 1
                seen.add(w)
        for w in seen:
            doc_freq[w] += 1
    n = max(1, len(sites))
    rows = [[w, c, round(c / n, 3), total[w],
             "table stakes" if c / n >= 0.5 else ("shared" if c > 1 else "owned by one")]
            for w, c in doc_freq.most_common(400)]
    book.add("Vocabulary", ["term", "sites_using", "share_of_sites", "total_mentions", "read"],
             rows, [24, 12, 14, 14, 16])

    # -- Sources -----------------------------------------------------------
    rows = [[s.get("url", ""), s.get("used_for", "")] for s in analysis.get("sources", [])]
    for domain, site in sites.items():
        rows.append([site.get("final_url") or "https://" + domain,
                     "site scan: %d pages" % len(site.get("pages", []))])
    book.add("Sources", ["url", "used_for"], rows, [70, 50])

    book.save(out_path)
    return {"workbook": os.path.abspath(out_path), "sheets": [s[0] for s in book.sheets],
            "companies": len(set(sites) | set(profiles)),
            "pages": sum(len(s.get("pages", [])) for s in sites.values()),
            "matrices": len(analysis.get("matrices", []))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="directory of scan_site.py JSON")
    ap.add_argument("--analysis", help="analysis.json with company profiles and matrices")
    ap.add_argument("--out", required=True, help="output .xlsx path")
    args = ap.parse_args()

    analysis = {}
    if args.analysis and os.path.exists(args.analysis):
        with open(args.analysis, encoding="utf-8") as fh:
            analysis = json.load(fh)
    analysis.setdefault("generated_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    print(json.dumps(build(args.data, analysis, args.out), indent=2))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
