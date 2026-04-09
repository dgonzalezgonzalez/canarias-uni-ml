# Indeed API Research

**Date:** 2026-04-09
**Status:** COMPLETED

## Endpoints Descubiertos

### Primary Data Source: Embedded JSON

Indeed embeds job listings as JSON within `<script>` tags in the HTML:

```javascript
window.mosaic.providerData["mosaic-provider-jobcards"] = {...};
```

**Extraction pattern:**
```python
import re, json

pattern = r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*({.*?});'
data = re.findall(pattern, html, re.DOTALL)
jobs = json.loads(data[0])['metaData']['mosaicProviderJobCardsModel']['results']
```

**Data structure:**
```json
{
  "metaData": {
    "mosaicProviderJobCardsModel": {
      "results": [
        {
          "jobkey": "abc123...",
          "title": "Software Engineer",
          "companyName": "Company Inc",
          "formattedLocation": "Las Palmas, ES",
          "salary": "€30,000 - €45,000 a year",
          "date": "Thu, 09 Apr 2026 12:00:00 GMT",
          ...
        }
      ]
    }
  }
}
```

### URL Patterns

- Search: `https://es.indeed.com/jobs?q={query}&l={location}&start={offset}`
- Detail: `https://es.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={jobkey}`
- Alternative: `https://www.indeed.com/viewjob?jk={jobkey}`

## Anti-Bot Status

**Cloudflare blocking confirmed** in this environment. The current `IndeedSpider` using Playwright is blocked at line 48 of `indeed.py`.

## Available Approaches

### Option 1: HTTP with Smart Headers (RISKY)
Using httpx with browser-like headers may bypass Cloudflare for some requests.
- Pros: Free, no external dependencies
- Cons: Unreliable, may block at any time

### Option 2: Third-Party Scraping APIs (RECOMMENDED)
Services that handle Cloudflare automatically:
- **ScrapingBee**: `https://app.scrapingbee.com/api/v1/`
- **Scrapingdog**: `https://api.scrapingdog.com/indeed`
- **Scrapingfly**: `https://api.scrapfly.io/scrape`
- **Oxylabs**: `https://realtime.oxylabs.io/v1/queries`

### Option 3: Indeed Publisher API (LIMITED)
Official API via `indeedlabs/indeed-python`:
- Requires publisher number (free registration)
- Limited to 100 requests/day
- Only returns basic data

## Recommendation

**Implemented: IndeedApiSpider with hybrid approach.**

1. **Primary**: httpx with embedded JSON extraction (fast, free)
2. **Fallback**: ScrapingBee API if `SCRAPINGBEE_API_KEY` is set
3. **Archive**: Original Playwright spider kept as last resort

## Implementation Status

- [x] IndeedApiSpider created with embedded JSON extraction
- [x] ScrapingBee fallback implemented
- [ ] ScrapingBee API key needed for production use

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SCRAPINGBEE_API_KEY` | No | ScrapingBee API key for Cloudflare bypass |

## Next Steps

1. Get ScrapingBee API key from https://app.scrapingbee.com
2. Set `SCRAPINGBEE_API_KEY` in `.env`
3. Test full pipeline with `--limit-per-source 50`

## References

- https://scrapfly.io/blog/posts/how-to-scrape-indeedcom
- https://smartproxy.io/blog/scrape-indeed-guide
- https://github.com/indeedlabs/indeed-python
