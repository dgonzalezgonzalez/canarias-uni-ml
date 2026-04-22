# Degree Sources

Initial degree-catalog path uses authoritative metadata fixtures shaped like ANECA and RUCT public records.

Planned live-source strategy:

- ANECA for title evaluation metadata and report provenance
- RUCT for official title registry fields
- university-hosted memory URLs as fallback when official surfaces omit direct PDF link

Current live implementation:

- ANECA search results are scraped per cycle (`grado`, `master`, `doctorado`) from the official title finder
- ANECA detail pages provide branch, center, credits, and official evaluation-report PDF links
- First-pass degree descriptions are extracted from ANECA evaluation reports, not yet from university-hosted memoria PDFs
- University memory resolvers are registered per Canary university (`ull`, `ulpgc`, `uec`, `uam`, `ufpc`) to backfill missing memoria links
- RUCT remains fixture-backed until its public contract is stabilized in code
