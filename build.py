#!/usr/bin/env python3
"""Rebel Detail & Valeting: static site build.

    python3 build.py               staging build (noindex everywhere, robots blocks all)
    python3 build.py --production  live build; fails if any [CONFIRM] or missing photo remains

Output goes to ./dist. A QA report is written to ./REPORT.md on every build.
Requires: Python 3.10+, Jinja2, Pillow.
"""
import datetime as dt
import hashlib
import html as htmllib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
PRODUCTION = "--production" in sys.argv
TODAY = dt.date.today()

def load(name):
    return json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))

SITE = load("business")
PKG = load("packages")
FAQS = load("faqs")
_R = load("reviews")
REVIEWS = sorted(_R["reviews"], key=lambda r: r["date"], reverse=True)
FB_COUNT = _R.get("facebook_review_count", len(REVIEWS))
WORK = load("work")["jobs"]
PACKAGES = [dict(PKG["packages"][k], id=k) for k in PKG["order"]]

# ---------------------------------------------------------------- pages
B_VAL = ("Valeting", "/valeting/")
B_DET = ("Detailing", "/detailing/")

PAGES = [
    dict(url="/", tpl="home.html", index=True, schema=["business", "website"],
         title="Rebel Detail & Valeting | Mobile Car Valeting, North Leeds",
         description="Mobile car valeting and detailing at your home or workplace across North Leeds. Valets from £40, open 7 days. Get a quote or message us on WhatsApp."),
    dict(url="/valeting/", tpl="valeting.html", index=True, crumbs=[B_VAL], schema=["valeting"],
         title="Mobile Car Valeting Leeds from £40 | Rebel Detail & Valeting",
         description="Mini, Full and Platinum valets carried out at your home or workplace in North Leeds. Every wash is by hand. Compare what's included, then book."),
    *[dict(url=f"/valeting/{p['slug']}/", tpl="package.html", index=True, pkg=p,
           crumbs=[B_VAL, (p["name"], f"/valeting/{p['slug']}/")], schema=["package"],
           title=p["title"], description=p["description"]) for p in PACKAGES],
    dict(url="/detailing/", tpl="detailing.html", index=True, crumbs=[B_DET],
         title="Car Detailing North Leeds: Polishing & Ceramic | Rebel",
         description="What detailing is, how it differs from valeting and which service your car needs: machine polishing to improve the paint, or a ceramic coating to protect it."),
    dict(url="/detailing/machine-polishing/", tpl="machine-polishing.html", index=True,
         crumbs=[B_DET, ("Machine polishing", "/detailing/machine-polishing/")], schema=["svc:Machine polishing and paint correction"],
         title="Machine Polishing & Paint Correction Leeds | Rebel",
         description="Swirls, haze and light scratches reduced by machine polishing, carried out at your home. What polishing can fix, what it can't, and how it works."),
    dict(url="/detailing/ceramic-coating/", tpl="ceramic-coating.html", index=True,
         crumbs=[B_DET, ("Ceramic coating", "/detailing/ceramic-coating/")], schema=["svc:Ceramic coating"],
         title="Ceramic Coating Leeds, Applied at Your Home | Rebel",
         description="What a ceramic coating does, what it doesn't, how the paint is prepared and how to look after it afterwards. Mobile ceramic coating in North Leeds."),
    dict(url="/vip/", tpl="vip.html", index=True, crumbs=[("Rebel VIP", "/vip/")], schema=["svc:Rebel VIP maintenance valeting"],
         title="Rebel VIP: Regular Car Valeting Membership | Rebel",
         description="Fortnightly or monthly maintenance valets at £35 a visit, after a first clean at the Full Valet price. Keep your car at the standard it was brought to."),
    dict(url="/our-work/", tpl="our-work.html", index=True, crumbs=[("Our work", "/our-work/")],
         title="Our Work: Valeting & Detailing Results in Leeds | Rebel",
         description="Real before-and-after results from cars we've valeted and detailed around North Leeds, with what each one needed and what was done."),
    dict(url="/reviews/", tpl="reviews.html", index=True, crumbs=[("Reviews", "/reviews/")],
         title="Customer Reviews | Rebel Detail & Valeting",
         description="What customers say about Rebel's mobile valeting and detailing in North Leeds, taken from Google and Facebook."),
    dict(url="/areas/", tpl="areas.html", index=True, crumbs=[("Areas we cover", "/areas/")],
         title="Areas We Cover: Leeds, Bradford & Harrogate | Rebel",
         description="Mobile car valeting and detailing across North Leeds, Aireborough, Shipley, Baildon, Harrogate and Knaresborough. See every area we cover."),
    dict(url="/about/", tpl="about.html", index=True, crumbs=[("About", "/about/")],
         title="Meet Connor | Rebel Detail & Valeting",
         description="The person behind Rebel Detail & Valeting: how the business started, how Connor works and what to expect when he arrives."),
    dict(url="/faq/", tpl="faq.html", index=True, crumbs=[("FAQ", "/faq/")],
         title="Mobile Valeting FAQs: Water, Weather, Timings | Rebel",
         description="Answers about water and power, bad weather, timings, payment and getting your car ready for a mobile valet."),
    dict(url="/contact/", tpl="contact.html", index=True, crumbs=[("Get a quote", "/contact/")], sticky=False,
         title="Get a Quote: Mobile Valeting Leeds | Rebel",
         description="Tell us your car, postcode and what it needs. Add photos for a faster quote, or message us on WhatsApp."),
    dict(url="/thank-you/", tpl="thank-you.html", index=False, sticky=False,
         title="Thanks, we've got your request | Rebel Detail & Valeting",
         description="Your quote request has been sent to Rebel Detail & Valeting. Send photos on WhatsApp to help us quote accurately."),
    dict(url="/privacy/", tpl="privacy.html", index=True, crumbs=[("Privacy policy", "/privacy/")],
         title="Privacy Policy | Rebel Detail & Valeting",
         description="How Rebel Detail & Valeting collects, uses and protects the information you give us when you ask for a quote or book."),
    dict(url="/cookies/", tpl="cookies.html", index=True, crumbs=[("Cookies", "/cookies/")],
         title="Cookie Policy | Rebel Detail & Valeting",
         description="Which cookies the Rebel Detail & Valeting website uses, why, and how you can control them."),
    dict(url="/booking-terms/", tpl="booking-terms.html", index=True, crumbs=[("Booking terms", "/booking-terms/")],
         title="Booking Terms | Rebel Detail & Valeting",
         description="Rebel Detail & Valeting's booking, payment, cancellation and bad-weather terms."),
    dict(url="/404.html", tpl="404.html", index=False,
         title="Page not found | Rebel Detail & Valeting",
         description="This page doesn't exist or has moved. See valet prices or get a quote from Rebel Detail & Valeting."),
]

# ---------------------------------------------------------------- helpers
CONFIRM_RE = re.compile(r"\[\[CONFIRM:\s*(.*?)\]\]", re.S)
_page_missing: list[str] = []

def confirm(text):
    return Markup(f'<mark class="confirm">[CONFIRM WITH REBEL: {escape(text)}]</mark>')

def rich(s):
    """Data strings are trusted HTML; turn [[CONFIRM: ...]] into visible markers."""
    if s is None:
        return ""
    return Markup(CONFIRM_RE.sub(lambda m: str(confirm(m.group(1))), str(s)))

def plain(s):
    """Strip confirm markers and tags (for meta/schema)."""
    s = CONFIRM_RE.sub("", str(s))
    return re.sub(r"<[^>]+>", "", s).strip()

def wa(text="Hi, I'd like a quote for my car."):
    return f"https://wa.me/{SITE['whatsapp']}?text={quote(text)}"

def file_hash(p: Path):
    return hashlib.md5(p.read_bytes()).hexdigest()[:8]

ASSET_HASH = {}
def asset(rel):
    return f"/assets/{rel}?v={ASSET_HASH.get(rel, 'dev')}"

# ---------------------------------------------------------------- images
IMG_MANIFEST = {}
WIDTHS = [480, 960, 1440, 1920]

def process_images():
    from PIL import Image, ImageOps
    src = ROOT / "source-images"
    out = DIST / "assets" / "img"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob("*")):
        if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        h8 = file_hash(f)
        widths = [w for w in WIDTHS if w < im.width * 0.9] + [min(im.width, WIDTHS[-1])]
        widths = sorted(set(widths))
        for w in widths:
            r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            r.save(out / f"{f.stem}-{h8}-{w}.webp", "WEBP", quality=78, method=6)
            r.save(out / f"{f.stem}-{h8}-{w}.jpg", "JPEG", quality=80, optimize=True, progressive=True)
        IMG_MANIFEST[f.stem] = dict(w=im.width, h=im.height, hash=h8, widths=widths)

def photo(slot, alt, ratio="4 / 3", sizes="(min-width: 60rem) 50vw, 100vw", eager=False, cls=""):
    m = IMG_MANIFEST.get(slot)
    if not m:
        _page_missing.append(f"{slot}: {alt}")
        return Markup(
            f'<div class="photo-slot {cls}" style="aspect-ratio:{ratio}" role="img" '
            f'aria-label="Photo to be added: {escape(alt)}"><span><strong>Photo to be added</strong>'
            f'{escape(alt)}<code>source-images/{escape(slot)}.jpg</code></span></div>')
    base = f"/assets/img/{slot}-{m['hash']}"
    webp = ", ".join(f"{base}-{w}.webp {w}w" for w in m["widths"])
    jpg = ", ".join(f"{base}-{w}.jpg {w}w" for w in m["widths"])
    largest = m["widths"][-1]
    h = round(m["h"] * largest / m["w"])
    load_attr = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return Markup(
        f'<picture class="{cls}"><source type="image/webp" srcset="{webp}" sizes="{sizes}">'
        f'<img src="{base}-{largest}.jpg" srcset="{jpg}" sizes="{sizes}" width="{largest}" height="{h}" '
        f'alt="{escape(alt)}" {load_attr} decoding="async"></picture>')

def before_after(slot, alt_before, alt_after, caption=""):
    b, a = IMG_MANIFEST.get(f"{slot}-before"), IMG_MANIFEST.get(f"{slot}-after")
    cap = f"<figcaption>{escape(caption)}</figcaption>" if caption else ""
    if b and a:
        return Markup(
            f'<figure class="ba" data-ba><div class="ba-frame">'
            f'<div class="ba-after">{photo(slot + "-after", alt_after, ratio="4 / 3")}</div>'
            f'<div class="ba-before">{photo(slot + "-before", alt_before, ratio="4 / 3")}</div>'
            f'<span class="ba-tag ba-tag-before" aria-hidden="true">Before</span>'
            f'<span class="ba-tag ba-tag-after" aria-hidden="true">After</span>'
            f'<input class="ba-range" type="range" min="0" max="100" value="50" '
            f'aria-label="Drag to compare before and after"></div>{cap}</figure>')
    return Markup(
        f'<figure class="ba-static"><div class="ba-pair">'
        f'<div>{photo(slot + "-before", alt_before)}<span class="ba-label">Before</span></div>'
        f'<div>{photo(slot + "-after", alt_after)}<span class="ba-label">After</span></div>'
        f'</div>{cap}</figure>')

def faqs_for(tag):
    return [f for f in FAQS if tag in f["tags"]]

def reviews_for(*tags, limit=3, fallback=True):
    """Reviews carrying any of the tags (newest first); topped up with short general ones if needed."""
    rs = [r for r in REVIEWS if not tags or set(tags) & set(r["tags"])]
    if fallback and len(rs) < limit:
        extra = [r for r in REVIEWS if r not in rs and ("general" in r["tags"] or "trade" in r["tags"]) and len(r["text"]) < 260]
        rs += extra[: limit - len(rs)]
    return rs[:limit]

# ---------------------------------------------------------------- schema
BUSINESS_ID = SITE["url"] + "/#business"

def area_served():
    towns = SITE["towns"] or [SITE["base_area"]]
    return [{"@type": "Place", "name": t} for t in towns]

def schema_business():
    days = []
    for h in SITE["hours"]:
        days.append({"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"],
                     "opens": h["opens"], "closes": h["closes"]})
    d = {"@context": "https://schema.org", "@type": "AutomotiveBusiness", "@id": BUSINESS_ID,
         "name": SITE["name"], "url": SITE["url"] + "/", "telephone": SITE["phone_e164"],
         "email": SITE["email"], "priceRange": SITE["price_range"], "areaServed": area_served(),
         "openingHoursSpecification": days,
         "sameAs": [s["url"] for s in SITE["social"] if s["confirmed"]]}
    if (ROOT / "static/assets/img/logo.png").exists():
        d["logo"] = SITE["url"] + "/assets/img/logo.png"
        d["image"] = SITE["url"] + "/assets/img/og-default.jpg"
    return d

def schema_website():
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE["url"] + "/#website",
            "name": SITE["name"], "url": SITE["url"] + "/", "inLanguage": "en-GB",
            "publisher": {"@id": BUSINESS_ID}}

def schema_service(name, url, description, price=None):
    d = {"@context": "https://schema.org", "@type": "Service", "name": name, "serviceType": name,
         "url": SITE["url"] + url, "description": plain(description),
         "provider": {"@id": BUSINESS_ID}, "areaServed": area_served()}
    if price is not None:
        d["offers"] = {"@type": "Offer", "price": f"{price:.2f}", "priceCurrency": "GBP", "url": SITE["url"] + url}
    return d

def schema_crumbs(crumbs):
    items = [("Home", "/")] + list(crumbs)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE["url"] + u}
                                for i, (n, u) in enumerate(items)]}

def build_schema(page):
    out = []
    for s in page.get("schema", []):
        if s == "business":
            out.append(schema_business())
        elif s == "website":
            out.append(schema_website())
        elif s == "valeting":
            for p in PACKAGES:
                out.append(schema_service(p["name"], f"/valeting/{p['slug']}/", p["summary"], p["price"]))
        elif s == "package":
            p = page["pkg"]
            out.append(schema_service(p["name"], page["url"], p["summary"], p["price"]))
        elif s.startswith("svc:"):
            out.append(schema_service(s[4:], page["url"], page["description"]))
    if page.get("crumbs"):
        out.append(schema_crumbs(page["crumbs"]))
    return [Markup(json.dumps(d, ensure_ascii=False, indent=1).replace("</", "<\\/")) for d in out]

# ---------------------------------------------------------------- build
def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST)
    for p in (DIST / "assets").rglob("*"):
        if p.is_file() and p.suffix in {".css", ".js"}:
            ASSET_HASH[str(p.relative_to(DIST / "assets"))] = file_hash(p)
    process_images()

    fonts = sorted(f.name for f in (DIST / "assets/fonts").glob("*.woff2"))
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]),
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.filters["rich"] = rich
    env.filters["plain"] = plain
    env.globals.update(site=SITE, packages=PACKAGES, features=PKG["features"], groups=PKG["groups"],
                       faqs=FAQS, work=WORK, fb_count=FB_COUNT, faqs_for=faqs_for, reviews_for=reviews_for, reviews=REVIEWS,
                       confirm=confirm, photo=photo, before_after=before_after, wa=wa, asset=asset,
                       year=TODAY.year, staging=not PRODUCTION, font_preloads=fonts[:2],
                       logo=(DIST / "assets/img/logo.png").exists(),
                       og_image=(DIST / "assets/img/og-default.jpg").exists())

    report = {"confirms": {}, "photos": {}, "qa": []}
    titles, descs = {}, {}
    built = {}
    for page in PAGES:
        page.setdefault("crumbs", None)
        page.setdefault("sticky", True)
        _page_missing.clear()
        html = env.get_template("pages/" + page["tpl"]).render(
            page=page, schema=build_schema(page), noindex=(not PRODUCTION) or not page["index"],
            canonical=SITE["url"] + page["url"])
        url = page["url"]
        out = DIST / (url.strip("/") or "") / "index.html" if url.endswith("/") else DIST / url.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        built[url] = html

        c = re.findall(r'<mark class="confirm">\[CONFIRM WITH REBEL: (.*?)\]</mark>', html, re.S)
        if c:
            report["confirms"][url] = [htmllib.unescape(re.sub(r"<[^>]+>", "", x)) for x in c]
        if _page_missing:
            report["photos"][url] = list(dict.fromkeys(_page_missing))
        # QA checks
        h1 = len(re.findall(r"<h1[\s>]", html))
        if h1 != 1:
            report["qa"].append(f"{url}: {h1} <h1> elements (expected 1)")
        if len(page["title"]) > 65:
            report["qa"].append(f"{url}: title is {len(page['title'])} chars")
        if not 70 <= len(page["description"]) <= 160:
            report["qa"].append(f"{url}: meta description is {len(page['description'])} chars")
        if page["title"] in titles:
            report["qa"].append(f"{url}: duplicate title with {titles[page['title']]}")
        if page["description"] in descs:
            report["qa"].append(f"{url}: duplicate description with {descs[page['description']]}")
        titles[page["title"]], descs[page["description"]] = url, url
        if re.search(r"<img(?![^>]*\balt=)[^>]*>", html):
            report["qa"].append(f"{url}: <img> without alt")

    # internal link check
    for url, html in built.items():
        for href in set(re.findall(r'href="(/[^"#?]*)', html)):
            target = DIST / href.lstrip("/")
            ok = (target / "index.html").exists() if href.endswith("/") else target.exists()
            if not ok:
                report["qa"].append(f"{url}: broken internal link {href}")

    # sitemap, robots, host files
    idx = [p for p in PAGES if p["index"]]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE['url']}{p['url']}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>" for p in idx]
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    robots = (f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n" if PRODUCTION
              else "# Staging build: do not index\nUser-agent: *\nDisallow: /\n")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    # items that appear on every page (footer etc.) are reported once
    pages_with = [set(v) for v in report["confirms"].values()]
    common = set.intersection(*pages_with) if len(pages_with) == len(PAGES) else set()
    if common:
        report["confirms"] = {"Sitewide (header/footer)": sorted(common),
                              **{u: [i for i in v if i not in common] for u, v in report["confirms"].items()}}
    write_report(report)
    blocking = report["confirms"] or report["photos"] or [q for q in report["qa"] if "broken" in q or "<h1>" in q]
    if PRODUCTION and blocking:
        print("PRODUCTION BUILD BLOCKED: unresolved items remain. See REPORT.md.")
        sys.exit(1)
    n_c = sum(len(v) for v in report["confirms"].values())
    n_p = sum(len(v) for v in report["photos"].values())
    print(f"Built {len(PAGES)} pages to dist/ ({'production' if PRODUCTION else 'staging'}). "
          f"{n_c} confirm markers, {n_p} photo slots, {len(report['qa'])} QA notes. See REPORT.md.")

def write_report(r):
    L = [f"# Build report ({'production' if PRODUCTION else 'staging'}, {TODAY.isoformat()})", ""]
    L += ["## QA checks", ""] + ([f"- {q}" for q in r["qa"]] or ["- All automated checks passed."]) + [""]
    L += ["## Facts to confirm with Rebel", ""]
    for url, items in r["confirms"].items():
        L.append(f"### {url}")
        L += [f"- [ ] {i}" for i in dict.fromkeys(items)] + [""]
    L += ["## Photos still needed", "", "Drop files into `source-images/` using the slot name, e.g. `source-images/home-hero.jpg`.", ""]
    for url, items in r["photos"].items():
        L.append(f"### {url}")
        L += [f"- [ ] {i}" for i in items] + [""]
    (ROOT / "REPORT.md").write_text("\n".join(L), encoding="utf-8")

if __name__ == "__main__":
    main()
