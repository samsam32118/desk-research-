#!/usr/bin/env python3
"""Run the competitor-landscape scanner through a real browser.

Some vendors -- Autodesk among them -- answer urllib with HTTP 403 from a bot
WAF, and answer a headless Chromium with the actual marketing page. The copy is
public either way; only the transport differs. This swaps the scanner's
transport and reuses everything else, so the JSON it writes is the same shape
scan_site.py writes and every downstream script keeps working.

    python3 browser_scan.py autodesk.com/products/forma-site-design \
        --out data/ --max-pages 12

robots.txt is still fetched plainly and still honoured; --delay still spaces
requests to one site.
"""
import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time

SKILL_SCRIPTS = pathlib.Path(
    os.environ.get("SKILL_SCRIPTS",
                   "/home/user/desk-research-/.claude/skills/competitor-landscape/scripts"))

spec = importlib.util.spec_from_file_location("scan_site", SKILL_SCRIPTS / "scan_site.py")
scan_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_site)

CHROME = os.environ.get("CHROME_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")


class BrowserFetcher(scan_site.Fetcher):
    """Same (final_url, status, text, ctype, error) contract, Chromium behind it."""

    def __init__(self, page, **kw):
        super().__init__(**kw)
        self.page = page

    def get(self, url, tries=2):
        # robots.txt is plain text and never WAF'd; keep it off the browser so
        # the parser sees the file, not a viewer page wrapped around it.
        if url.rstrip("/").endswith("robots.txt"):
            return super().get(url, tries=tries)
        last_err = ""
        for attempt in range(tries):
            self._wait()
            try:
                resp = self.page.goto(url, wait_until="domcontentloaded",
                                      timeout=int(self.timeout * 1000))
                status = resp.status if resp else 0
                # Marketing pages hydrate after DOMContentLoaded; give the H1 a
                # moment to appear rather than extracting an empty shell.
                try:
                    self.page.wait_for_selector("h1", timeout=4000)
                except Exception:                        # noqa: BLE001
                    self.page.wait_for_timeout(1200)
                html = self.page.content()
                final = self.page.url
                ctype = ((resp.header_value("content-type") or "") if resp else "") or "text/html"
                if status >= 400:
                    return final, status, "", ctype, "HTTP %s" % status
                return final, status, html, ctype.lower(), ""
            except Exception as e:                       # noqa: BLE001
                last_err = "%s: %s" % (type(e).__name__, str(e).split("\n")[0][:160])
                if attempt + 1 < tries:
                    time.sleep(1.0)
        return url, 0, "", "", last_err


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-pages", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--delay", type=float, default=0.8)
    ap.add_argument("--ignore-robots", action="store_true")
    ap.add_argument("--include-case-studies", action="store_true")
    ap.add_argument("--also-urls", default="")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    also = [u.strip() for u in args.also_urls.split(",") if u.strip()]

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME,
                                    args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(user_agent=UA, locale="en-US",
                                  viewport={"width": 1440, "height": 900})
        # Images and fonts carry no headings; skipping them makes the scan fast
        # and lighter on the sites being read.
        ctx.route("**/*", lambda route: route.abort()
                  if route.request.resource_type in ("image", "media", "font")
                  else route.continue_())
        page = ctx.new_page()
        for target in args.targets:
            fetcher = BrowserFetcher(page, ua=UA, timeout=args.timeout, delay=args.delay,
                                     respect_robots=not args.ignore_robots)
            try:
                rec = scan_site.scan_company(
                    target, fetcher, max_pages=args.max_pages,
                    include_case_studies=args.include_case_studies, also_urls=also)
            except Exception as e:                       # noqa: BLE001
                rec = {"slug": scan_site.slugify(target), "input": target, "domain": target,
                       "reachable": False, "pages": [], "notes": ["crash: %s" % e],
                       "headings_found": 0}
            (out / ("%s.json" % rec["slug"])).write_text(
                json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
            results.append(rec)
        ctx.close()
        browser.close()

    print(json.dumps({
        "companies": len(results),
        "reachable": sum(1 for r in results if r.get("reachable")),
        "pages": sum(len(r.get("pages", [])) for r in results),
        "out": str(out),
        "unreachable": [r["domain"] for r in results if not r.get("reachable")],
    }, indent=2))


if __name__ == "__main__":
    sys.exit(main())
