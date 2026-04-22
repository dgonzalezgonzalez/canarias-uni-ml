# Source Normalization

Canonical job dimensions now keep both normalized values and raw scraped source fields.

## Geography

- Normalize municipality first when a trusted alias exists.
- Infer island and province from municipality reference map when possible.
- Preserve unresolved raw values for audit and alias-table expansion.

## Contract Type

- Canonical values: `indefinido`, `temporal`, `formacion`, `fijo_discontinuo`, `autonomo`, `other`.
- Preserve original raw label in `contract_type_raw`.
