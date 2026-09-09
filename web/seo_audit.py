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


def validate_page(html, url):
    head = html.split("</head>", 1)[0]
    canonical = re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"', head)
    assert list(map(unescape, canonical)) == [url], (url, canonical)
    title = re.findall(r"<title>(.*?)</title>", head, re.S)
    assert len(title) == 1 and title[0].strip(), url
    description = re.findall(r'<meta\s+name="description"\s+content="([^"]*)"', head)
    assert len(description) == 1 and description[0].strip(), url
    assert 'name="robots" content="index,follow' in head, url
    assert len(re.findall(r"<h1(?:\s|>)", html)) == 1, url
    if len(sys.argv) == 1:
        images = re.findall(r'<meta\s+property="og:image"\s+content="([^"]+)"', head)
        assert len(images) == 1 and images[0].startswith(origin + "/social/"), url
        image_path = Path(".svelte-kit/cloudflare") / unquote(urlsplit(images[0]).path).lstrip("/")
        with image_path.open("rb") as image:
            png = image.read(24)
        assert png[:8] == b"\x89PNG\r\n\x1a\n", image_path
        assert int.from_bytes(png[16:20], "big") == 1200, image_path
        assert int.from_bytes(png[20:24], "big") == 630, image_path
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', head, re.S
    )
    assert len(blocks) == 1, url
    data = json.loads(blocks[0])
    assert data["@context"] == "https://schema.org", url
    graph = data["@graph"]
    pages = [item for item in graph if item["@type"] in ("WebPage", "CollectionPage")]
    assert len(pages) == 1, url
    page = pages[0]
    assert page["@id"] == url + "#webpage" and page["url"] == url, url
    assert page["name"] == unescape(title[0]), url
    assert page["description"] == unescape(description[0]), url
    for relation in ("mainEntity", "breadcrumb"):
        if relation in page:
            assert any(item.get("@id") == page[relation]["@id"] for item in graph), url
    return title, graph, page


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
person_markup_count = 0
samples = {}
visited_files = set()
for url in urls:
    path = local_file(url, html=True)
    visited_files.add(path)
    html = path.read_text()
    title, graph, page = validate_page(html, url)
    titles[unescape(title[0])] += 1
    if urlsplit(url).path.startswith("/instructors/"):
        people = [item for item in graph if item["@type"] == "Person"]
        assert len(people) == 1, url
        person = people[0]
        assert person["@id"] == url + "#person" and person["url"] == url, url
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1)
        assert unescape(re.sub(r"<[^>]*>", "", h1)).strip() == person["name"].strip(), (
            url
        )
        assert page["mainEntity"] == {"@id": person["@id"]}, url
        person_markup_count += 1

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
# Audit every other generated HTML page as well, including prerequisite maps.
additional_pages = set()
noindex_pages = 0
for path in root.rglob("*.html"):
    if path in visited_files:
        continue
    html = path.read_text()
    head = html.split("</head>", 1)[0]
    if '<meta http-equiv="refresh"' in head:
        continue  # SvelteKit also publishes these redirects in _redirects.
    if 'name="robots" content="noindex,follow"' in head:
        noindex_pages += 1
        continue
    canonical = re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"', head)
    assert len(canonical) == 1, path
    url = unescape(canonical[0])
    assert url.startswith(origin + "/"), (path, url)
    validate_page(html, url)
    if url not in urls:
        additional_pages.add(url)

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
            "additional_indexable_pages": len(additional_pages),
            "noindex_html_pages": noindex_pages,
            "courses": course_count,
            "courses_with_course_markup": course_markup_count,
            "instructors_with_person_markup": person_markup_count,
            "department_catalogs": len(catalog_urls),
            "noindex_rankings": noindex_rankings,
            "all_courses_linked": True,
            "duplicate_title_groups": sum(count > 1 for count in titles.values()),
            "samples": samples,
        },
        indent=2,
    )
)
