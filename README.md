# Rebel Detail & Valeting: website

A static, multi-page site generated from templates and data files. There's no framework and no client-side rendering, so every page is plain HTML that search engines can read directly.

## Build

Requires Python 3.10+ with Jinja2 and Pillow (`pip install jinja2 pillow`).

```
python3 build.py               # staging: noindex on every page, robots.txt blocks all
python3 build.py --production  # live: refuses to build while anything in REPORT.md is unresolved
```

The output goes to `dist/`. Every build writes `REPORT.md`, which lists:

- facts to confirm with Rebel, by page
- photo slots still empty
- automated QA results: one H1 per page, title and description lengths, duplicates, missing alt text and broken internal links

## Where things live

| To change… | Edit |
| --- | --- |
| Phone, email, hours, socials, towns, Google rating, GA4 ID | `data/business.json` |
| Prices, times, inclusions, package copy and FAQs | `data/packages.json` (feeds the cards, comparison table, package pages and schema) |
| General FAQs | `data/faqs.json` (tags decide which pages show each one) |
| Reviews | `data/reviews.json` (genuine, word for word, with the service) |
| Page text | `templates/pages/*.html` |
| Header, footer, mobile bar | `templates/partials/` |
| Page titles, descriptions and URLs | `PAGES` list in `build.py` |
| Styles and scripts | `static/assets/css/site.css`, `static/assets/js/site.js` |

Unconfirmed facts are written as `[[CONFIRM: …]]` in data files or `{{ confirm("…") }}` in templates. They show as highlighted text on staging builds.

## Photos

Save originals into `source-images/` named after their slot. The current slot names are listed in `REPORT.md`, for example `home-hero.jpg`, `home-ba-1-before.jpg` and `home-ba-1-after.jpg`. The build then:

- creates 480, 960, 1440 and 1920px WebP and JPEG versions with hashed filenames
- adds width and height (no layout shift), and lazy loads below the fold
- turns any `*-before` / `*-after` pair into an accessible drag slider

Use real Rebel photos only.

## Fonts and logo

- Download **Barlow** (400, 600) and **Barlow Condensed** (600, 700) as woff2 from Google Fonts (SIL Open Font License). Save them in `static/assets/fonts/` as `barlow-400.woff2`, `barlow-600.woff2`, `barlow-condensed-600.woff2` and `barlow-condensed-700.woff2`. They're self-hosted, so no requests go to Google.
- Save the logo as `static/assets/img/logo.svg`. It replaces the temporary "REBEL" wordmark and is used as the favicon and in the schema.
- Save a 1200×630 share image as `static/assets/img/og-default.jpg`.

## Hosting (Netlify recommended)

- Build command `python3 build.py --production`, publish directory `dist`.
- The quote form uses Netlify Forms, including photo uploads and a spam honeypot. Set up email notifications to rebelvalet@gmail.com in Netlify's form settings. Test a multi-photo upload before launch.
- `_redirects` sends the old `/privacy-policy` URL to `/privacy/`. `_headers` sets caching and security headers.
- Point the domain at Netlify by changing the DNS at GoDaddy. Keep the existing Google Search Console verification.

## After launch

- Submit `https://rebelvalet.co.uk/sitemap.xml` in Search Console.
- Update the website link and opening hours on the Google Business Profile, Facebook, Nextdoor, Yell and Click Valet so they match the site.
- To enable GA4, add the ID to `business.json`. The consent banner and these events then switch on: `phone_click`, `whatsapp_click`, `quote_cta`, `package_select`, `vip_cta` and `quote_submit`.
