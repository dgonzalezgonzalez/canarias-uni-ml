---
title: Completar scrapers InfoJobs e Indeed
type: feat
status: active
date: 2026-04-09
origin: docs/brainstorms/2026-04-09-complete-infojobs-and-indeed-scrapers-requirements.md
---

# Completar Scrapers InfoJobs e Indeed

## Overview

Completar los spiders de InfoJobs (usando API oficial) e Indeed (reverse-engineering de API interna) para maximizar cobertura de ofertas de empleo en Canarias.

## Problem Frame

El pipeline tiene 4 fuentes objetivo. SCE y Turijobs funcionan. InfoJobs tiene spider de API existente pero incompleto. Indeed está bloqueado por Cloudflare incluso con Playwright.

## Requirements Trace

- R1. InfoJobs API spider produce `SpiderResult` válidos
- R2. Indeed spider (nuevo) use endpoints JSON descubiertos
- R3. Fallback: API InfoJobs si el spider falla, spider actual Indeed si el nuevo falla
- R4. Integración en CLI existente sin romper fuentes existentes

## Scope Boundaries

- No goal: Web scraping de InfoJobs (bloqueado por robots.txt)
- No goal: Garantizar 100% cobertura

## Context & Research

### Relevant Code and Patterns

- `src/canarias_jobs/spiders/base.py` — Spider Protocol y SpiderResult
- `src/canarias_jobs/spiders/infojobs.py` — Spider API existente (requiere credenciales)
- `src/canarias_jobs/spiders/indeed.py` — Spider actual (bloqueado por Cloudflare)
- `src/canarias_jobs/models.py` — JobRecord con 24 campos
- `src/canarias_jobs/utils.py` — clean_text, parse_date, infer_province_from_island

### External References

- InfoJobs API v9: `https://api.infojobs.net/api/9/offer`
- Indeed bloqueado por Cloudflare en este entorno

## Key Technical Decisions

- **InfoJobs API como primario**: El spider existente usa API oficial v9 con autenticación Basic. Requiere `INFOJOBS_CLIENT_ID` y `INFOJOBS_CLIENT_SECRET`.
- **Indeed reverse-engineering**: Investigar endpoints JSON internos que Indeed usa para renderizar resultados. Fallback al spider actual si no se encuentran endpoints accesibles.
- **Spiders coexisten**: No se elimina código existente. Fallback integrado en cada spider.

## Open Questions

### Resolved During Planning

- **InfoJobs robots.txt conflict**: Resuelto — se usa API oficial (subdominio `api.infojobs.net`) en lugar de web scraping público. Las reglas de robots.txt del dominio principal no aplican al API.

### Deferred to Implementation

- ¿Indeed permite acceso a endpoints sin cookies de sesión? (requiere investigación con browser devtools)
- ¿Qué versión exacta de la API InfoJobs está en uso? (la v9 puede no ser la última)

## Implementation Units

- [ ] **Unit 1: Investigar y verificar InfoJobs API**

**Goal:** Verificar que el spider InfoJobs existente funciona con las credenciales proporcionadas

**Requirements:** R1

**Dependencies:** Credenciales InfoJobs en `.env`

**Files:**
- Modify: `src/canarias_jobs/spiders/infojobs.py`
- Test: `tests/test_infojobs.py`

**Approach:**
1. Verificar presencia de `INFOJOBS_CLIENT_ID` y `INFOJOBS_CLIENT_SECRET` en entorno
2. Hacer request de prueba al endpoint `/api/9/offer` con provinces `las-palmas` y `santa-cruz-de-tenerife`
3. Si falla, diagnosticar: auth error, rate limit, endpoint changed
4. Ajustar spider si es necesario

**Patterns to follow:**
- `src/canarias_jobs/spiders/infojobs.py` (spider actual)
- `src/canarias_jobs/spiders/sce.py` (manejo de errores de API)

**Test scenarios:**
- Happy path: API responde con lista de ofertas de Canarias → SpiderResult contains records
- Edge case: API returns empty list → SpiderResult with empty records (not error)
- Error path: Credenciales inválidas → SpiderError descriptivo
- Error path: Rate limit (429) → SpiderError con mensaje de retry
- Error path: Network timeout → SpiderError

**Verification:**
- `python -m src.canarias_jobs.cli --sources infojobs --limit-per-source 10` produce CSV con registros válidos

---

- [ ] **Unit 2: Investigar endpoints Indeed**

**Goal:** Descubrir endpoints JSON internos de Indeed que permitan extraer ofertas sin pasar por Cloudflare

**Requirements:** R2

**Dependencies:** None

**Files:**
- Modify: `src/canarias_jobs/spiders/indeed.py` (nuevo spider o extensión)

**Approach:**
1. Investigar con browser devtools (Playwright con logging de red):
   - Navegar a `https://es.indeed.com/jobs?q=&l=canarias`
   - Capturar todas las peticiones XHR/fetch
   - Identificar endpoints que retornan JSON con datos de empleo
2. Documentar endpoints descubiertos y su estructura
3. Probar si los endpoints funcionan sin cookies de sesión
4. Definir cutoff: si no hay endpoints públicos tras investigación, documentar y archivar

**Patterns to follow:**
- `src/canarias_jobs/spiders/sce.py` (extracción de JWT, manejo de API)
- `src/canarias_jobs/spiders/turijobs.py` (uso de sitemap/alternatives)

**Test scenarios:**
- Research output: Lista de endpoints descubiertos con estructura de datos
- Research output: Documentación de endpoints que requieren auth vs públicos
- Edge case: Endpoints requieren cookies específicas → Documentar y proponer fallback

**Verification:**
- Documento en `docs/indeed-api-research.md` con:
  - Endpoints descubiertos
  - Estructura de respuesta
  - Requisitos de autenticación
  - Recomendación: proceed o archive

---

- [ ] **Unit 3: Implementar IndeedSpider con endpoints descubiertos**

**Goal:** Implementar spider Indeed basado en endpoints JSON si fueron descubiertos

**Requirements:** R2, R3

**Dependencies:** Unit 2 (investigación)

**Files:**
- Create: `src/canarias_jobs/spiders/indeed_api.py` (o modificar `indeed.py`)
- Test: `tests/test_indeed_api.py`

**Approach:**
1. Si Unit 2 descubre endpoints públicos:
   - Implementar `IndeedApiSpider` con esos endpoints
   - Normalizar respuesta a JobRecord
   - Integrar como fallback en el flujo existente
2. Si Unit 2 no encuentra endpoints:
   - Agregar logging detallado al spider actual
   - Documentar que Indeed está bloqueado por Cloudflare
   - Marcar spider como "best-effort"

**Patterns to follow:**
- `src/canarias_jobs/spiders/infojobs.py` (manejo de API, normalización)
- `src/canarias_jobs/spiders/sce.py` (autenticación, manejo de tokens)

**Test scenarios:**
- Happy path: Endpoints responden → JobRecord extraction works
- Edge case: Endpoints return different schema → graceful handling
- Error path: Endpoints return 403/401 → fallback to current spider
- Integration: CLI includes Indeed results in CSV

**Verification:**
- `python -m src.canarias_jobs.cli --sources indeed --limit-per-source 10` produce resultados

---

- [ ] **Unit 4: Agregar tests de regresión**

**Goal:** Asegurar que cambios no rompen fuentes existentes

**Requirements:** R4

**Dependencies:** Units 1 y 3 completos

**Files:**
- Create: `tests/test_infojobs.py`
- Create: `tests/test_indeed.py`
- Modify: `tests/conftest.py` (si existe)

**Approach:**
1. Crear tests con respuestas de API mockeadas (sample-based approach recomendado)
2. Testear parsing de respuesta JSON → JobRecord
3. Testear normalización de campos (provincia, isla, salario)
4. Testear manejo de errores

**Patterns to follow:**
- AGENTS.md: "Sample-based tests where possible"
- pytest conventions

**Test scenarios:**
- InfoJobs: Parse response → verify all JobRecord fields
- InfoJobs: Missing optional fields → graceful handling
- Indeed: API response parsing (si endpoints descubiertos)
- Regression: All sources work together in CLI

**Verification:**
- `pytest tests/` pasa sin errores

## System-Wide Impact

- **CLI integration**: `--sources` flag puede especificar `infojobs` o `indeed`
- **CSV output**: Nuevos registros se integran sin duplicados (por `external_id`)
- **Error propagation**: Spiders fallan graceful, CLI continúa con otras fuentes

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| InfoJobs API credentials no disponibles | Documentar requisitos en README |
| InfoJobs API cambia versión/endpoint | Monitorear errores, adaptar |
| Indeed endpoints requieren cookies/sesión | Fallback al spider actual, documentar |
| Indeed endpoints desaparecen sin aviso | Mantener spider actual como fallback |

## Documentation / Operational Notes

- Actualizar README.md con requisitos de credenciales InfoJobs
- Crear `docs/indeed-api-research.md` con hallazgos de investigación
- Documentar en `docs/source-notes.md` el estado de cada fuente

## Sources & References

- **Origin document:** [docs/brainstorms/...requirements.md](docs/brainstorms/2026-04-09-complete-infojobs-and-indeed-scrapers-requirements.md)
- InfoJobs API: `https://api.infojobs.net/api/9/offer`
- Indeed: `https://es.indeed.com/jobs?l=canarias`
