# Template Workbook

The public Local Wealth-Tracker Agent can generate a clean synthetic Template Workbook. `setup` creates it automatically, and it is a supported starting point for your own tracker; it is not copied from the owner's private tracker.

## Template Workbook Version

- `template_id`: `local-wealth-tracker-template`
- `template_version`: `1.0`
- `workbook_kind`: `synthetic_template`
- `template_schema`: `net-worth-v1`
- Sheet name: `Net worth` (change with `--sheet-name` on `create`)
- Metadata sheet: `Template Metadata`
- Default Tracker Currency: `DKK`

The `Template Metadata` sheet is hidden and contains the version contract that workbook adapters validate before treating the workbook as a supported public template. Workbooks without this metadata, with a different template ID, or with an unsupported `template_version` must be rejected by template validation.

Generate the template with:

```bash
uv run wealth-tracker template-workbook create \
  --output "templates/local-wealth-tracker-template.xlsx" \
  --tracker-currency DKK \
  --start-year 2026
```

## Supported V1 Customization

Known template dimensions can be customized with:

```bash
uv run wealth-tracker template-workbook customize \
  --template "templates/local-wealth-tracker-template.xlsx" \
  --output "templates/local-wealth-tracker-template-custom.xlsx" \
  --tracker-currency EUR \
  --rename "Living expenses=Household costs" \
  --rename "Groceries (monthly)=Groceries"
```

Supported v1 customization is limited to:

- renaming existing category labels and section labels,
- changing the Tracker Currency stored in visible template cells and hidden metadata,
- using setup profile path overrides for known private local directories,
- creating future period columns through the existing workbook planner against the supported template schema.

Unsupported formula changes, arbitrary layout edits, missing metadata, unknown labels, duplicate labels, blank labels, and unsupported template versions are rejected. The agent should explain the unsupported edit and stop; it must not imply that it can repair arbitrary spreadsheets.

## Synthetic Structure

The template uses the same supported workbook dimensions as the current planner:

- category labels in column `B`,
- year header in row `2`,
- month header in row `3`,
- 12 month columns from `Jan` through `Dec`,
- a merged year header over the month block,
- empty leaf-category cells for user financial values,
- formulas for parent and derived rows.

The v1 template contains generic section labels and leaf rows:

- `Income (net)` with `Full-time job (net)` and `Other income`.
- `Cashflow` as a derived row.
- `Living expenses` with `Rent (monthly)`, `Groceries (monthly)`, and `Transportation`.
- `Services` with `Mobile phone (monthly)`, `Internet (monthly)`, and `Cloud services`.
- `Insurance` with `Insurance (monthly)`.
- `Investments` with `Brokerage contributions` and `Pension contributions`.
- `Assets` with `Cash savings`, `Brokerage account`, and `Pension account`.
- `Total net worth` as a derived row.

The template contains no real values, no private categories, no personal sheet names, no private proxy split assumptions, no Category Memory, and no Importer Profiles.

## V1 Customization Boundary

Setup and template commands may customize known workbook dimensions such as categories, section labels, period columns, currency settings, and profile paths. Formula and layout customization are out of scope for v1 until workbook schemas and template versions make those changes safe. The one supported structural change is a new leaf row you approve on the monthly Exception Sheet: on commit it is inserted at the end of its parent section in the tracker, with formulas shifted and the parent `SUM` expanded; if the parent formula is not a simple `SUM`, nothing is written (see [ADR 0006](adr/0006-formula-aware-leaf-row-insertion.md)).

The original Tracker Workbook safety rules still apply to template-based workbooks: formula-owned cells, populated manual cells, derived rows, fixed rows, section totals, unsupported rows, unsupported columns, and ambiguous structure are not direct write targets.
