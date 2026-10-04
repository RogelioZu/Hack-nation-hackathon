# Nota de procedencia: hash de EXP-001 en estas propuestas

Estos artefactos registran como `sha256` de `reports/experiments/EXP-001/result.json` el hash de los bytes
**observados en la corrida**, que eran una copia con finales LF. **No es el hash canónico de EXP-001.**

- Observado en la corrida (copia LF): `3113a9eecf8d7458cc482c78da9e47386ec574b976f094ccdbb8dbde59c384aa`
- **Canónico certificado** (`reports/experiments/EXP-001/validation.json` → `result_sha256`): `5e4084a346049a31091d887a803248a4497f1f542ab68498dd6f5dae04b56b28`

El contenido es idéntico: los mismos datos con finales CRLF reproducen exactamente el hash certificado.
Desde el 2026-10-04, el archivo de la rama tiene esos bytes certificados (commit `2bd1fbf` en `main`).
Las herramientas guardan ahora `observed_sha256` y `certified_sha256` por separado.

Los artefactos no se reescriben: nunca se sobrescriben, y los bytes de las hipótesis están certificados
en `reports/discovery/local/reviews/REV-001.json`.

| Artefacto | Campo | `integrity` registrado |
|---|---|---|
| `PROP-003.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `PROP-005.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `PROP-008.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `PROP-009.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `superseded/PROP-001.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `superseded/PROP-002.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `superseded/PROP-004.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `superseded/PROP-006.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
| `superseded/PROP-007.json` | `provenance.source_artifacts[3].sha256` | (sin campo integrity) |
