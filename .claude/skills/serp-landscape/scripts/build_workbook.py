#!/usr/bin/env python3
"""Turn the run into an Excel workbook.

Eight sheets, each answering a different question:

  Keywords     every keyword in the universe -- where it came from, its topic,
               and for the sampled ones what kind of SERP it returns
  SERP results one row per keyword per position: the URL, the title Google
               showed, the title the page actually carries, and its meta
               description. This is the sheet people asked for
  Pages        one row per unique ranking URL, with everything measured about it
  Domains      share of voice across the sampled SERPs
  Clusters     keyword groups Google answers with the same pages
  Matrices     every plotted coordinate with the evidence behind it
  Titles       the words winning titles use, against the words in the queries
  Sources      what produced each part of the dataset

Writes a real .xlsx with the standard library only -- no openpyxl, no pandas,
so it runs anywhere.

Usage:
    python3 build_workbook.py --metrics metrics.json --keywords keywords.json \\
        --serp serp.json --out espresso-serp.xlsx
    python3 build_workbook.py --metrics metrics.json --analysis analysis.json --out out.xlsx
"""

import argparse
import json
import os
import re
import zipfile
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
                if value is None or value == "" or isinstance(value, bool):
                    if isinstance(value, bool):
                        cells.append('<c r="%s" s="2" t="inlineStr"><is><t>%s</t></is></c>'
                                     % (ref, "yes" if value else "no"))
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
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
                 'relationships+xml"/>',
                 '<Default Extension="xml" ContentType="application/xml"/>',
                 '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
                 'officedocument.spreadsheetml.sheet.main+xml"/>',
                 '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-'
                 'officedocument.spreadsheetml.styles+xml"/>']
        for i in range(1, n + 1):
            types.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType='
                         '"application/vnd.openxmlformats-officedocument.spreadsheetml.'
                         'worksheet+xml"/>' % i)
        types.append("</Types>")

        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
                '2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>']

        wb = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              "<sheets>"]
        for i, (name, _, _, _) in enumerate(self.sheets, start=1):
            wb.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (esc(name), i, i))
        wb.append("</sheets></workbook>")

        wbrels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                  'relationships">']
        for i in range(1, n + 1):
            wbrels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
                          'officeDocument/2006/relationships/worksheet" '
                          'Target="worksheets/sheet%d.xml"/>' % (i, i))
        wbrels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
                      'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                      "</Relationships>" % (n + 1))

        styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                  '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
                  '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
                  '<fills count="3"><fill><patternFill patternType="none"/></fill>'
                  '<fill><patternFill patternType="gray125"/></fill>'
                  '<fill><patternFill patternType="solid"><fgColor rgb="FF1F3B57"/>'
                  '<bgColor indexed="64"/></patternFill></fill></fills>'
                  '<borders count="1"><border/></borders>'
                  '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
                  "</cellStyleXfs>"
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
                z.writestr("xl/worksheets/sheet%d.xml" % i,
                           self._sheet_xml(headers, rows, widths))
        return path


def load(path, default=None):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return default if default is not None else {}


def join(values, sep=" | ", limit=12):
    return sep.join(str(v) for v in (values or [])[:limit])


def quadrant(x, y):
    return "%s-%s" % ("top" if (y or 0) >= 5 else "bottom", "right" if (x or 0) >= 5 else "left")


def build(metrics, keywords, serp, analysis, out_path):
    book = MiniXlsx()
    kw_rows = metrics.get("keywords", {})
    page_rows = metrics.get("pages", {})
    universe = keywords.get("keywords", [])
    topic_label = {c["id"]: c["label"] for c in keywords.get("clusters", [])}
    topic_size = {c["id"]: c["size"] for c in keywords.get("clusters", [])}

    # -- Keywords: the whole universe, not just the sampled ones -----------
    headers = ["keyword", "level", "topic", "topic_size", "source", "found_via_probe",
               "suggest_rank", "suggest_relevance", "words", "is_question", "intent_prior",
               "serp_captured", "serp_intent", "intent_agrees", "serp_cluster",
               "demand_mass", "results", "readable_results", "coverage_pct",
               "distinct_domains", "incumbent_share", "median_word_count",
               "median_title_len", "median_desc_len", "median_age_days",
               "share_listicle", "share_title_year", "kw_in_title", "top_domains"]
    rows = []
    for k in universe:
        kw = k["keyword"]
        m = kw_rows.get(kw, {})
        rows.append([
            kw, k.get("level", ""), topic_label.get(k.get("cluster", ""), ""),
            topic_size.get(k.get("cluster", ""), ""), k.get("source", ""), k.get("probe", ""),
            k.get("rank", ""), k.get("relevance", ""), k.get("words", ""),
            k.get("is_question", False), k.get("intent_prior", ""),
            bool(m), m.get("serp_intent", ""), m.get("intent_agrees", "") if m else "",
            m.get("serp_cluster", ""), m.get("demand_mass", ""), m.get("results", ""),
            m.get("readable_results", ""), m.get("coverage_pct", ""),
            m.get("distinct_domains", ""), m.get("incumbent_share", ""),
            m.get("median_word_count", ""), m.get("median_title_len", ""),
            m.get("median_desc_len", ""), m.get("median_age_days", ""),
            m.get("share_listicle", ""), m.get("share_title_year", ""),
            m.get("kw_in_title", ""), join(m.get("top_domains"), ", ", 5),
        ])
    # Keywords with SERPs first: that is where the analysis lives.
    rows.sort(key=lambda r: (r[11] is not True, -(r[15] or 0) if isinstance(r[15], (int, float))
                             else 0, r[0]))
    if not rows:                                          # no universe file: fall back to SERPs
        rows = [[kw, "", "", "", "", "", "", "", m.get("words", ""), "", m.get("intent_prior", ""),
                 True, m.get("serp_intent", ""), m.get("intent_agrees", ""),
                 m.get("serp_cluster", ""), m.get("demand_mass", ""), m.get("results", ""),
                 m.get("readable_results", ""), m.get("coverage_pct", ""),
                 m.get("distinct_domains", ""), m.get("incumbent_share", ""),
                 m.get("median_word_count", ""), m.get("median_title_len", ""),
                 m.get("median_desc_len", ""), m.get("median_age_days", ""),
                 m.get("share_listicle", ""), m.get("share_title_year", ""),
                 m.get("kw_in_title", ""), join(m.get("top_domains"), ", ", 5)]
                for kw, m in kw_rows.items()]
    book.add("Keywords", headers, rows,
             [42, 6, 16, 10, 16, 26, 8, 10, 6, 9, 13, 9, 13, 9, 11, 11, 7, 8, 9, 8, 10, 11,
              10, 10, 10, 9, 10, 9, 40])

    # -- SERP results: the sheet the whole thing is for --------------------
    headers = ["keyword", "rank", "domain", "url", "serp_title", "page_title",
               "title_rewritten_by_google", "meta_description", "page_kind", "word_count",
               "h2_count", "title_len", "desc_len", "title_has_number", "title_year",
               "published", "modified", "schema_types", "readable", "http_status",
               "keywords_this_page_ranks_for", "visibility_share"]
    rows = []
    for kw, entry in sorted(serp.get("keywords", {}).items()):
        for r in entry.get("results", []):
            p = page_rows.get(r["url"], {})
            rows.append([
                kw, r.get("rank"), r.get("domain", ""), r.get("url", ""),
                r.get("serp_title", ""), p.get("title", ""),
                p.get("title_rewritten_by_google", ""), p.get("meta_description", ""),
                p.get("page_kind", ""), p.get("word_count", ""), p.get("h2_count", ""),
                p.get("title_len", ""), p.get("desc_len", ""), p.get("title_number", ""),
                p.get("title_year", ""), p.get("published", ""), p.get("modified", ""),
                join(p.get("schema_types"), ", ", 6), p.get("readable", ""),
                p.get("status", ""), p.get("keywords_ranked", ""), p.get("visibility_share", ""),
            ])
    book.add("SERP results", headers, rows,
             [40, 5, 22, 60, 55, 55, 10, 70, 14, 9, 7, 8, 8, 9, 8, 11, 11, 30, 8, 7, 9, 9])

    # -- Pages -------------------------------------------------------------
    headers = ["url", "domain", "page_kind", "keywords_ranked", "best_position",
               "avg_position", "visibility_share", "title", "meta_description", "h1",
               "word_count", "h2_count", "tables", "lists", "images", "title_len", "desc_len",
               "title_has_number", "title_year", "title_question", "brand_in_title",
               "kw_in_title", "published", "modified", "age_days", "has_faq_schema",
               "schema_types", "readable", "http_status", "ranks_for"]
    rows = []
    for p in sorted(page_rows.values(), key=lambda p: -p["visibility"]):
        rows.append([
            p["url"], p["domain"], p["page_kind"], p["keywords_ranked"], p["best_position"],
            p["avg_position"], p["visibility_share"], p["title"], p["meta_description"],
            p["h1"], p["word_count"], p["h2_count"], p["tables"], p["lists"], p["images"],
            p["title_len"], p["desc_len"], p["title_number"], p["title_year"],
            p["title_question"], p["title_brandtail"], p["kw_in_title"], p["published"],
            p["modified"], p["age_days"], p["has_faq_schema"],
            join(p["schema_types"], ", ", 8), p["readable"], p["status"],
            join(p["ranks_for"], " ; ", 25),
        ])
    book.add("Pages", headers, rows,
             [60, 22, 14, 9, 8, 8, 9, 55, 70, 45, 9, 7, 6, 6, 6, 8, 8, 9, 8, 9, 9, 8, 11, 11,
              8, 9, 30, 8, 7, 70])

    # -- Domains -----------------------------------------------------------
    headers = ["domain", "keywords_ranked", "urls", "visibility_share", "avg_position",
               "mostly", "readable_pages"]
    rows = [[d["domain"], d["keywords_ranked"], d["urls"], d["visibility_share"],
             d["avg_position"], d["top_kind"], d["readable_pages"]]
            for d in metrics.get("domains", [])]
    book.add("Domains", headers, rows, [30, 10, 7, 10, 9, 16, 9])

    # -- Clusters ----------------------------------------------------------
    headers = ["cluster", "head_keyword", "keywords", "demand_mass", "serp_intent",
               "shared_pages", "members"]
    rows = [[c["id"], c["head"], c["size"], c["demand_mass"], c["serp_intent"],
             join(c.get("shared_pages"), " ; ", 4), join(c["members"], " ; ", 40)]
            for c in metrics.get("serp_clusters", [])]
    book.add("Clusters", headers, rows, [9, 42, 8, 11, 13, 60, 90])

    # -- Matrices ----------------------------------------------------------
    headers = ["matrix_id", "matrix_title", "unit", "x_axis", "x_metric", "x_low", "x_high",
               "y_axis", "y_metric", "y_low", "y_high", "point", "x", "y", "quadrant",
               "quadrant_label", "evidence"]
    rows = []
    for m in analysis.get("matrices", []):
        x, y = m.get("x", {}), m.get("y", {})
        quads = m.get("quadrants", {})
        key = {"top-right": "tr", "top-left": "tl", "bottom-right": "br", "bottom-left": "bl"}
        for pt in m.get("points", []):
            q = quadrant(pt.get("x"), pt.get("y"))
            rows.append([m.get("id", ""), m.get("title", ""), m.get("unit", "keyword"),
                         x.get("label", ""), x.get("metric", "judged"), x.get("low", ""),
                         x.get("high", ""), y.get("label", ""), y.get("metric", "judged"),
                         y.get("low", ""), y.get("high", ""), pt.get("id", ""), pt.get("x"),
                         pt.get("y"), q, quads.get(key[q], ""), pt.get("evidence", "")])
    book.add("Matrices", headers, rows,
             [14, 38, 8, 22, 18, 22, 22, 22, 18, 22, 22, 42, 6, 6, 12, 24, 80])

    # -- Titles ------------------------------------------------------------
    headers = ["term", "titles_using", "share_of_ranking_titles", "times_in_keywords", "read"]
    rows = []
    for v in metrics.get("title_vocabulary", []):
        if v["share_of_titles"] >= 0.5:
            read = "table stakes"
        elif v["in_keywords"] and not v["titles_using"]:
            read = "asked for, not written"
        elif v["in_keywords"]:
            read = "matches the query"
        else:
            read = "added by the writer"
        rows.append([v["term"], v["titles_using"], v["share_of_titles"], v["in_keywords"], read])
    book.add("Titles", headers, rows, [24, 11, 13, 12, 22])

    # -- Sources -----------------------------------------------------------
    headers = ["source", "detail", "used_for"]
    rows = [["autocomplete", "%s via %s" % (keywords.get("locale", ""),
                                            join(keywords.get("sources"), ", ")),
             "%d keywords from %d API calls" % (len(universe), keywords.get("api_calls", 0))],
            ["search engine", metrics.get("engine", ""),
             "%d SERPs, top %d" % (len(kw_rows), metrics.get("top_n", 10))],
            ["page fetch", "direct HTTP, robots.txt honoured",
             "%d unique URLs, %d readable"
             % (len(page_rows), metrics.get("summary", {}).get("readable_pages", 0))]]
    for s in analysis.get("sources", []):
        rows.append([s.get("source", "manual"), s.get("url", ""), s.get("used_for", "")])
    book.add("Sources", headers, rows, [20, 60, 60])

    book.save(out_path)
    return {"workbook": os.path.abspath(out_path), "sheets": [s[0] for s in book.sheets],
            "keyword_rows": len(universe) or len(kw_rows),
            "serp_rows": sum(len(e.get("results", []))
                             for e in serp.get("keywords", {}).values()),
            "page_rows": len(page_rows), "matrices": len(analysis.get("matrices", []))}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--keywords", help="keywords.json, for the full universe sheet")
    ap.add_argument("--serp", help="serp.json, for the per-position sheet")
    ap.add_argument("--analysis", help="analysis.json, for the Matrices sheet")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    metrics = load(args.metrics)
    analysis = load(args.analysis)
    analysis.setdefault("generated_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    print(json.dumps(build(metrics, load(args.keywords), load(args.serp), analysis, args.out),
                     indent=2))


if __name__ == "__main__":
    main()
