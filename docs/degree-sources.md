# Degree Sources

Initial degree-catalog path uses authoritative metadata fixtures shaped like ANECA and RUCT public records.

Planned live-source strategy:

- ANECA for title evaluation metadata and report provenance
- RUCT for official title registry fields
- university-hosted memory URLs as fallback when official surfaces omit direct PDF link

Current live implementation:

- ANECA search results are scraped per cycle (`grado`, `master`, `doctorado`) from the official title finder
- ANECA detail pages provide branch, center, credits, and official evaluation-report PDF links
- Memoria URL resolution is attempted directly on university pages first (per-university resolver map)
- Degree `description` is extracted from memoria PDFs only by default; ANECA resolution reports are not used for description unless explicitly enabled in code
- University memory resolvers are registered per Canary university (`ull`, `ulpgc`, `uec`, `uam`, `ufpc`) to backfill missing memoria links
- RUCT remains fixture-backed until its public contract is stabilized in code
