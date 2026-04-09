---
date: 2026-04-09
topic: complete-infojobs-and-indeed-scrapers
---

# Completar Scrapers de InfoJobs e Indeed

## Problem Frame

El pipeline de scraping de empleo en Canarias tiene dos fuentes incompletas:
- **InfoJobs**: El spider actual usa la API oficial que requiere credenciales. Se prefiere scraping directo del sitio web para evitar dependencias de API.
- **Indeed**: Bloqueado por Cloudflare incluso con Playwright. El reverse-engineering de la API interna puede evitar este bloqueo.

Completar ambas fuentes aumenta significativamente la cobertura de ofertas de empleo en Canarias.

## Requirements

**InfoJobs — Web Scraping**

- R1. Crear nuevo spider InfoJobs basado en scraping web del sitio (fuente primaria)
- R2. Usar herramienta HTML→Markdown (sugerencia: `crawl4ai` por ser open source y LLM-friendly)
- R3. Extraer campos `JobRecord`: título, empresa, descripción, salario (texto), ubicación, tipo contrato, fecha publicación
- R4. Mantener la inferencia de isla a partir de provincia/municipio
- R5. El spider API existente (`InfoJobsSpider`) se mantiene como fallback
- R6. Definir estrategia de fallback: intentar web scraping primero, usar API si falla
- R7. Verificar robots.txt antes de implementar

**Indeed — Reverse-Engineering API**

- R8. Investigar las llamadas XHR/fetch que Indeed realiza cuando se navega el sitio
- R9. Implementar nuevo spider que use los endpoints JSON descubiertos
- R10. Manejar autenticación/cookies si los endpoints requieren sesión
- R11. Extraer todos los campos `JobRecord` con la misma calidad que fuentes existentes
- R12. Definir cutoff de éxito: si no se encuentran endpoints JSON públicos en investigación inicial, archivar y documentar el bloqueo
- R13. El spider actual (`IndeedSpider`) se mantiene como fallback; no se elimina código existente

## Success Criteria

- Ambos spiders (`infojobs.py`, `indeed.py`) producen `SpiderResult` válidos
- Los registros se integran correctamente en el CSV final sin duplicados
- El CLI existente (`--limit-per-source 50`) incluye datos de ambas fuentes
- No se introducen errores en las fuentes que ya funcionan (SCE, Turijobs)

## Scope Boundaries

- **No goal**: Mantener la implementación actual de API para InfoJobs como fallback permanente
- **No goal**: Garantizar 100% de cobertura (sitios pueden tener protecciones insuperables)

## Key Decisions

- **InfoJobs → HTML→Markdown**: Evita dependencia de credenciales API, reduce fragility de selectores CSS
- **Indeed → Reverse-engineering API**: Evita Cloudflare bypass, datos más estructurados
- **Agentes paralelos**: Ambos spiders se implementan concurrentemente para eficiencia

## Dependencies / Assumptions

- D1: `crawl4ai` o alternativa gratuita instalable en el entorno actual
- D2: Indeed tiene endpoints JSON accesibles sin autenticación o con cookies públicas
- D3: InfoJobs permite scraping de listado y detalle de ofertas

## Trade-offs Documentados

- **InfoJobs**: Scraping web vs API — se pierde estructura de datos (salary_min/max separados vs texto libre)
- **Indeed**: Endpoints no documentados pueden cambiar sin aviso — requiere mantenimiento activo

## Outstanding Questions

### Resolve Before Planning

- [Affects R2][Technical] Verificar que `pip install crawl4ai` funciona en el entorno actual
- [Affects R7][Technical] Verificar robots.txt de infojobs.net para scraping

### Deferred to Planning

- [Affects R9][Needs research] ¿Qué herramientas de browser inspection usar para capturar llamadas XHR de Indeed?
- [Affects R12][Needs research] ¿Indeed permite acceso a endpoints sin cookies de sesión?

## Next Steps

-> /ce:plan para planificación estructurada de implementación
