"""Validate the built SEO surface: python3 web/seo_audit.py [build directory]."""

import gzip
import json
import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from xml.etree import ElementTree

root = Path(
    sys.argv[1] if len(sys.argv) > 1 else ".svelte-kit/output/prerendered/pages"
)
origin = "https://uwcourses.com"
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def locations(path):
    return [node.text for node in ElementTree.parse(path).findall(".//s:loc", ns)]


def local_file(url, html=False):
    parsed = urlsplit(url)
    assert f"{parsed.scheme}://{parsed.netloc}" == origin, url
    assert not parsed.query and not parsed.fragment, url
    path = unquote(parsed.path).lstrip("/")
    return root / ((path + ".html") if path and html else path or "index.html")


sitemaps = locations(root / "sitemap.xml")
urls = []
for sitemap in sitemaps:
    path = local_file(sitemap)
    entries = locations(path)
    assert len(entries) <= 5000 and path.stat().st_size < 50 * 1024 * 1024, path
    urls.extend(entries)
assert len(set(urls)) == len(urls), "Duplicate sitemap URLs"

course_urls = set()
catalog_links = set()
catalog_urls = set()
department_catalog_links = set()
titles = Counter()
course_titles = set()
course_count = 0
course_markup_count = 0
samples = {}
for url in urls:
    path = local_file(url, html=True)
    html = path.read_text()
    head = html.split("</head>", 1)[0]
    canonical = re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"', head)
    assert list(map(unescape, canonical)) == [url], (url, canonical)
    title = re.findall(r"<title>(.*?)</title>", head, re.S)
    assert len(title) == 1 and title[0].strip(), url
    titles[unescape(title[0])] += 1
    description = re.findall(r'<meta\s+name="description"\s+content="([^"]*)"', head)
    assert len(description) == 1 and description[0].strip(), url
    assert 'name="robots" content="index,follow' in head, url
    assert len(re.findall(r"<h1(?:\s|>)", html)) == 1, url
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', head, re.S
    )
    assert len(blocks) == 1, url
    data = json.loads(blocks[0])
    assert data["@context"] == "https://schema.org", url
    graph = data["@graph"]
    course = next((item for item in graph if item["@type"] == "Course"), None)
    if urlsplit(url).path.startswith("/courses/") and not url.endswith(
        ("/easiest", "/hardest")
    ):
        course_count += 1
        course_urls.add(url)
        assert course or "No catalog description available." in html, url
    if course:
        course_markup_count += 1
        assert course["url"] == url and course["name"] and course["courseCode"], url
        assert course["name"] in unescape(html), url
        assert course["provider"]["name"] == "University of Wisconsin–Madison", url
        assert "UW–Madison" in unescape(title[0]), url
        assert title[0] not in course_titles, url
        course_titles.add(title[0])
    links = {
        origin + unescape(link)
        for link in re.findall(r'<a\b[^>]*href="(/[^"?#]*)"', html)
    }
    if url.endswith("/catalog"):
        catalog_urls.add(url)
        catalog_links.update(links)
    elif "/departments/" in url:
        department_catalog_links.update(links)
    if url in [
        origin + "/",
        origin + "/courses/COMPSCI_300",
        origin + "/departments/COMPSCI/catalog",
    ]:
        samples[url] = {
            "html_bytes": path.stat().st_size,
            "gzip_bytes": len(gzip.compress(html.encode())),
        }
assert course_urls <= catalog_links, (
    f"Courses missing catalog links: {course_urls - catalog_links}"
)
assert catalog_urls <= department_catalog_links, (
    "Catalog pages missing department links"
)
noindex_rankings = 0
for ranking in [
    *root.glob("departments/*/easiest.html"),
    *root.glob("departments/*/hardest.html"),
]:
    if (
        'name="robots" content="noindex,follow"'
        in ranking.read_text().split("</head>", 1)[0]
    ):
        noindex_rankings += 1
        url = (
            origin
            + "/"
            + quote(str(ranking.relative_to(root).with_suffix("")), safe="/")
        )
        assert url not in urls, url
if len(sys.argv) == 1:
    headers = Path(".svelte-kit/cloudflare/_headers").read_text()
    assert re.search(r"/data/\*\n[ \t]+X-Robots-Tag: noindex", headers), (
        "Missing data noindex header"
    )
    for pattern in ["/__data.json", "/*/__data.json"]:
        assert pattern + "\n  X-Robots-Tag: noindex" in headers, pattern
    redirects = Path(".svelte-kit/cloudflare/_redirects").read_text().splitlines()
    for old, target in [("/subjects", "/departments"), ("/stats", "/departments")]:
        assert f"{old} {target} 308" in redirects, f"Missing redirect: {old}"
print(
    json.dumps(
        {
            "sitemaps": len(sitemaps),
            "indexable_urls": len(urls),
            "courses": course_count,
            "courses_with_course_markup": course_markup_count,
            "department_catalogs": len(catalog_urls),
            "noindex_rankings": noindex_rankings,
            "all_courses_linked": True,
            "duplicate_title_groups": sum(count > 1 for count in titles.values()),
            "samples": samples,
        },
        indent=2,
    )
)
