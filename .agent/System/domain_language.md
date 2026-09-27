# Domain Language

Shared language for PersonalWorthTracker domain decisions.

## Language

**Monthly Tracker Workbook Updater**:
A tool that proposes or writes monthly category totals into the existing tracker workbook from statement data.
_Avoid_: Personal finance ledger, accounting system

**Local Wealth-Tracker Agent**:
A local-first assistant that guides setup and maintenance of a template-based wealth tracker using deterministic automation, review artifacts, and optional review-only local model suggestions.
_Avoid_: Autonomous finance agent, remote AI finance app, generic accounting system

**Tracker Workbook**:
The existing spreadsheet that remains the source of truth for net worth and monthly category values.
_Avoid_: Ledger database, canonical transaction store

**Template Excel Workbook**:
A supported starter workbook schema that users may customize through known categories, sections, period columns, currency settings, and profile paths.
_Avoid_: Arbitrary spreadsheet, unsupported formula layout

**Statement Import Assistant**:
A local model-assisted importer that attempts to transform unknown financial statement formats into normalized transaction review artifacts.
_Avoid_: Trusted parser, arbitrary bank support, direct workbook input

**Trusted Statement Adapter**:
A deterministic parser for a known statement format whose normalized transactions can enter monthly planning after validation.
_Avoid_: LLM guess, unsupported statement format

**Authority**:
The per-row decision, `auto` or `review`, of whether a categorized transaction may reach the Tracker Workbook without the operator. Workbook cells derive from row authority.
_Avoid_: Cell blocking

**Exception Sheet**:
The `Review Required` sheet listing rows in review, suggestion prefilled, then rows already decided with the decision prefilled; one per month, rewritten by each `monthly` run. Blank accepts the suggestion; `NONE` rejects it.
_Avoid_: Whole-month review workbook

**Carried Decision**:
A Monthly Review Decision or Audit correction read from the Exception Sheet and written back, prefilled, when `monthly` rewrites it, so it keeps applying without another save (ADR 0003).
_Avoid_: Replayed decision

**Atomic Month Commit**:
Commit mode writes the Tracker Workbook, in place after a backup, only when zero rows remain in review, so it never holds a partial month.
_Avoid_: Unreviewed bucket, partial commit

**Commit Ledger**:
The category amounts each committed month wrote into the Tracker Workbook (`data/commit_ledger.json`). On a re-commit, a cell still holding its ledger amount is tool-owned and may be rewritten or cleared; any other value is a manual value (ADR 0007).
_Avoid_: Write log, commit history

**Trust Policy**:
The single pure module that decides Authority from evidence (tier, model votes, agreement), row facts (amount), and settings (`auto_max_amount`, `min_agreement`, `never_auto_categories`).
_Avoid_: Confidence threshold check, scattered review rules

**Untrusted Imported Transaction**:
A transaction extracted from an unknown or model-assisted statement import that requires user review before it can affect monthly planning or workbook updates.
_Avoid_: Parsed transaction, auto-write candidate

**Importer Profile**:
A local source-specific mapping learned from a user-confirmed import that helps parse similar future statements.
_Avoid_: Public bank parser, raw LLM memory, universal format support

**Educated Import Guess**:
A suggested field mapping or transaction categorization made from a confirmed importer profile, shown to the user with confidence before it is trusted.
_Avoid_: Automatic import decision, hidden parser rule, workbook write permission

**Tracker Currency**:
The currency used by tracker workbook values, currently DKK.
_Avoid_: Display-only label mismatch, source currency

**Workbook Cleanup Task**:
A deliberate one-off edit to workbook structure, labels, or other non-monthly value content.
_Avoid_: Monthly planning run, automatic financial update

**Reporting Month**:
The explicit year and month selected for a run of the updater.
_Avoid_: Run month, current month, previous month

**Period Column**:
A tracker workbook column representing one reporting month under a year header.
_Avoid_: Source statement period, run date

**Planned Structure Change**:
A proposed workbook shape change, such as adding a missing period column, shown for review before commit.
_Avoid_: Silent workbook mutation, value update

**Template Period Column**:
The immediately previous period column used as the source for formulas and formatting when creating a new period column.
_Avoid_: Separate template sheet, stale template column

**Year Block**:
A contiguous set of 12 period columns under one year header in the tracker workbook.
_Avoid_: Single missing month, unrelated columns

**Copied Manual Value**:
A non-formula value carried over from a template period column during structure creation.
_Avoid_: New month actual, formula

**Manual Workbook Value**:
An existing user-maintained value already present in a tracker workbook cell for the reporting month.
_Avoid_: Stale value, overwrite target

**Pre-Filled Recurring Value**:
A recurring tracker workbook value entered ahead of time for an expected fixed payment.
_Avoid_: Auto-write target, statement-derived total

**Carry-Forward Recurring Row**:
A configured recurring row whose pre-filled value may be retained when creating new period columns.
_Avoid_: Inferred fixed row, copied actual

**Fixed Row**:
A protected tracker workbook row that automated value writes should not overwrite.
_Avoid_: Carry-forward permission, recurring template

**Statement Total**:
The monthly category total calculated from parsed statement transactions.
_Avoid_: Ledger balance, truth source

**Same-Month Refund**:
A positive transaction in the same reporting month that reverses or reduces spending for a matched category.
_Avoid_: Cross-month adjustment, inferred reimbursement

**Later-Month Refund**:
A refund that appears in a later reporting month than the original purchase.
_Avoid_: Retroactive adjustment, prior-month correction

**Expense Claim**:
An identifiable reimbursement-like cashflow that maps to the tracker workbook's existing expense claim row.
_Avoid_: Ledger offset, inferred refund

**Proxy Split Transfer**:
A single bank-statement transfer to an intermediary account or service that is used as source evidence for multiple underlying tracker category allocations.
_Avoid_: Itemized ledger transaction, ordinary internal transfer

**Proxy Split Allocation**:
One configured category allocation carved out of a proxy split transfer.
_Avoid_: Separate bank transaction, inferred category guess

**Proxy Split Source Line**:
The original bank-statement transaction retained for audit after proxy split allocation, but excluded from direct workbook totals.
_Avoid_: Counted expense row, discarded source evidence

**Proxy Split Allocation Line**:
A categorized output line for one configured allocation carved out of a proxy split source line.
_Avoid_: Original bank transaction, hidden calculation

**Proxy Split Line ID**:
A deterministic identifier for a proxy split allocation or residual line, derived from the source transaction ID, split rule, and split role.
_Avoid_: Random review row ID, fake bank transaction ID

**Proxy Split Conversion Rate**:
A user-maintained fixed conversion rate used to convert configured proxy split allocation amounts into tracker currency.
_Avoid_: Live exchange rate, inferred Revolut rate

**Proxy Split Base Amount**:
A configured source-currency amount in a proxy split allocation before applying the proxy split conversion rate.
_Avoid_: Tracker-currency value, inferred residual

**Residual Split Amount**:
The remaining portion of a proxy split transfer after configured or reviewed allocations have been carved out.
_Avoid_: Hidden auto-category, ignored cash movement

**Residual Review Line**:
A review-required line representing the residual split amount from a proxy split transfer, linked to the original source transaction.
_Avoid_: Untracked remainder, separate source transaction

**Proxy Split Trigger**:
The configured transaction match criteria and minimum tracker-currency amount required before a proxy split transfer can allocate fixed category amounts.
_Avoid_: Partial split, weak merchant guess

**Monthly Proxy Split Limit**:
A rule limit that controls how many same-month candidate transactions may receive the same recurring proxy split automatically before additional candidates require review.
_Avoid_: Duplicate family allocation, silent repeated split

**Deterministic Category Match**:
A category assignment made by an explicit historical, recurring, amount/date, or keyword rule.
_Avoid_: Guess, fuzzy match

**Review-Only Transaction**:
A transaction that may be reported with a suggestion but must not be written automatically.
_Avoid_: Auto-write candidate

**Local LLM Mode**:
On-device model-assisted categorization (always on in `monthly`, opt-in in the per-month command) that processes minimized transaction context locally and returns suggestions that stay review-only unless Consensus and the Trust Policy grant `auto`.
_Avoid_: Remote API mode, deterministic rule

**Suggester**:
The port every category model sits behind: `suggest(rows, context) -> suggestions`, with Ollama, Fake and Consensus adapters.
_Avoid_: LLM client, provider

**Consensus**:
The Suggester adapter that asks two local models per row and records each answer as a vote; the Trust Policy grants `auto` only when enough distinct models agree.
_Avoid_: Ensemble, majority vote, confidence threshold

**Hosted Judgment**:
A category answer from a model hosted off the machine (e.g. TypeSafe Jev), sent only through `outbound_redaction`.
_Avoid_: Remote LLM Mode, cloud suggestion

**LLM Category Suggestion**:
A model-generated candidate category for a review-only transaction, limited to an existing leaf category, a **Subscription Leaf Proposal**, or NONE, and requiring user confirmation before it can affect workbook writes or Category Memory unless Consensus grants the row `auto`.
_Avoid_: Deterministic Category Match, Confirmed Review Decision, automatic category

**Allowed Category Set**:
The current YAML-validated leaf categories supplied as the only valid category choices for an LLM category suggestion.
_Avoid_: Free-form category list, workbook section rows, invented categories

**LLM Prompt Context**:
The minimized transaction and category data passed to a local model for review-only categorization, defaulting to the raw statement merchant text, amount, date, direction, and the allowed category set. Memory neighbours are matched and shown by normalised merchant identity.
_Avoid_: Full raw bank statement, account numbers, audit log dump

**Confirmed Review Decision**:
A user-approved category assignment for a review-only transaction.
_Avoid_: Model guess, unconfirmed match

**Parent/Section Row**:
A tracker workbook row that groups or totals child rows and is not a valid transaction category target.
_Avoid_: Manual category target, subcategory

**Leaf Category Row**:
A tracker workbook row under a parent or section that can receive source-backed transaction values, current-month manual review decisions, and Category Memory learning.
_Avoid_: Section total, derived row

**Category Registry**:
The YAML-backed category source that records parent, leaf, derived, alias, and allowed-new-child rules.
_Avoid_: Workbook-only category truth, hidden category list

**New Leaf Category Request**:
A manual review row that fills `new_parent_category` and `new_leaf_category` to add a missing leaf category after registry validation.
_Avoid_: Overloaded manual_category, automatic alias creation

**Subscription Leaf Proposal**:
A Suggester answer naming a new leaf `<Service> subscription` under `Services` for a recurring subscription with no leaf of its own; always `review`, and accepting it on the Exception Sheet becomes a **New Leaf Category Request**. Subscriptions get one leaf per service, never a generic bucket.
_Avoid_: Subscriptions leaf, new_leaf_candidate

**Category Memory**:
Private local categorization knowledge learned when a month commits, each entry with provenance `human` (confirmed decision) or `auto` (consensus result, trusted after two committed months).
_Avoid_: Public rule, self-trained guess

**Reviewed Decision File**:
A user-reviewed file containing confirmed category decisions ready to import into category memory.
_Avoid_: Raw review report, automatic guess output

**Local Rule**:
A hand-written private categorization rule maintained by the user.
_Avoid_: Learned mapping, generated memory

**Guidance Alias**:
A hand-written private merchant pattern mapped to a leaf category, matched directly after `human` **Category Memory** and shown to the **Suggester**; kept in ignored `config/guidance_aliases.local.yaml`.
_Avoid_: Alias (tracker label alias), learned mapping

**Merchant Identity**:
A normalized merchant-like name used for repeat categorization without changing reference numbers or sensitive account details.
_Avoid_: Full transaction description, account number

**Recurring Match Hint**:
An optional amount and date-window constraint attached to category memory for recurring payments.
_Avoid_: Mandatory rule, exact transaction copy

**Bank Statement**:
A statement source that proves cash movements in a bank account for the reporting month.
_Avoid_: Asset valuation source, investment statement

**Investment Statement**:
A statement source that proves investment holdings, asset values, or portfolio balances for the reporting month.
_Avoid_: Bank statement, cashflow statement, Nordea account statement

**Monthly Planning Run**:
A run that gathers available evidence for one reporting month and produces one proposed tracker workbook update set.
_Avoid_: Ledger close, account reconciliation

**Cross-Source Mismatch**:
A disagreement between source records that refer to related financial activity but prove different evidence types.
_Avoid_: Auto-reconciled correction, source override

**Cashflow Row**:
A tracker workbook category whose monthly value is derived from cash movement.
_Avoid_: Asset row, holding value

**Net Salary Income**:
The salary cash deposit visible on the bank statement.
_Avoid_: Gross salary, tax amount, labour market contribution

**Salary Multi-Match**:
More than one salary-like deposit matched in the same reporting month.
_Avoid_: Normal single salary write, automatic bonus handling

**Payroll Deduction Row**:
A tracker workbook category for tax or labour market contribution values maintained by workbook formula or manual payroll logic.
_Avoid_: Bank deposit category, inferred salary split, required salary statement source

**Derived Workbook Row**:
A tracker workbook row whose value is calculated by workbook formula or workbook-owned logic.
_Avoid_: Direct write target, statement total row

**Leaf Workbook Row**:
A tracker workbook row that can receive a source-backed value directly when workbook safety checks pass.
_Avoid_: Section total, derived row

**Asset Value Row**:
A tracker workbook category whose monthly value represents the value of an asset or holding.
_Avoid_: Cashflow row, transfer amount

**Holding Value**:
The month-end value of one specific investment holding shown by an investment statement.
_Avoid_: Account total, guessed allocation

**Portfolio Total Value**:
The month-end total value of an investment account or portfolio.
_Avoid_: Holding value, split allocation

**Digital Asset Value**:
The value of a crypto or other digital asset holding from a dedicated valuation source.
_Avoid_: Bank transfer, brokerage holding

**Month-End Market Value**:
The value of an investment holding or portfolio at the end of the reporting month.
_Avoid_: Contribution amount, transaction total, unit count

**Fixed Conversion Rate**:
A user-maintained exchange rate used to convert investment statement values into tracker currency.
_Avoid_: Live FX rate, market rate fetch

**Applied Conversion Rate**:
The exact fixed conversion rate recorded for a specific reporting month run.
_Avoid_: Current default rate, unstated assumption

**Investment Contribution**:
Cash moved into an investment account during the reporting month.
_Avoid_: Market value, asset value

**Internal Transfer**:
Cash movement between accounts owned by the user.
_Avoid_: Expense, income

**Credit Card Settlement**:
A payment that reduces a credit card liability.
_Avoid_: Expense category, card purchase

**Card Purchase**:
An itemized transaction made on a credit card.
_Avoid_: Credit card settlement, liability payment

## Relationships

- A **Monthly Tracker Workbook Updater** updates one **Tracker Workbook**.
- A **Tracker Workbook** contains monthly category values, not canonical transaction history.
- A **Tracker Workbook** uses one **Tracker Currency** for workbook values.
- A **Workbook Cleanup Task** is separate from a **Monthly Planning Run**.
- A **Reporting Month** identifies exactly one target month column in the **Tracker Workbook**.
- A **Reporting Month** should resolve to one existing or safely creatable **Period Column**.
- A missing **Period Column** should first appear as a **Planned Structure Change** in dry-run output.
- A new **Period Column** should use the immediately previous **Template Period Column** as its copy source.
- A missing year should create a full **Year Block** when the prior year pattern is clear.
- A **Copied Manual Value** should be cleared from newly created period cells unless it is deliberately handled as intended pre-filled content.
- A **Carry-Forward Recurring Row** is the only kind of non-formula value that may be retained during period/year creation.
- A **Fixed Row** controls overwrite protection and is separate from **Carry-Forward Recurring Row** permission.
- A **Statement Total** can propose an update to an empty workbook cell, but a **Manual Workbook Value** remains authoritative when the cell is already populated.
- A **Same-Month Refund** can reduce a **Statement Total** only when it has a deterministic category match.
- A **Later-Month Refund** is recorded in the reporting month where it appears and does not reopen prior months.
- An **Expense Claim** can map to the existing `Expense claims` row when deterministically identified.
- A **Proxy Split Transfer** may allocate one source transaction across multiple **Leaf Category Row** targets when the split is explicit.
- A **Proxy Split Source Line** should remain visible for audit while being excluded from direct workbook totals.
- A **Proxy Split Allocation Line** contributes to workbook planning through its target **Leaf Category Row**.
- A **Proxy Split Line ID** lets review decisions target split allocations and residuals without pretending they are separate bank transactions.
- A **Proxy Split Allocation** contributes to its configured **Leaf Category Row** while preserving the original source transaction reference.
- A configured **Proxy Split Allocation** is a **Deterministic Category Match** for its target **Leaf Category Row**.
- A **Proxy Split Transfer** may use a configured **Proxy Split Conversion Rate** to calculate tracker-currency allocations.
- A **Proxy Split Base Amount** is converted into the **Tracker Currency** before it contributes to a **Statement Total**.
- A **Proxy Split Trigger** must match the intermediary transaction and the transaction amount must cover all configured allocations.
- A **Monthly Proxy Split Limit** can require review when multiple candidate transactions match the same proxy split rule in one reporting month.
- A **Residual Split Amount** remains review-only unless the user supplies a separate category decision.
- A **Residual Review Line** should use the same source transaction with a split-specific identifier so the user can categorize the leftover amount separately.
- A **Residual Review Line** should not create **Category Memory** because the residual is a leftover allocation, not a stable merchant identity.
- A **Pre-Filled Recurring Value** is a kind of **Manual Workbook Value** and remains untouched by default.
- A **Deterministic Category Match** can support an automatic write only when all workbook safety checks also pass.
- A **Review-Only Transaction** can appear in reports but does not contribute to an automatic workbook write.
- A **Parent/Section Row** may appear in workbook context and review option metadata, but it must not be selected as a transaction category.
- A **Leaf Category Row** is the normal target for `manual_category`, workbook value planning, and Category Memory learning.
- The **Category Registry** is the durable source for deciding whether a category is parent, leaf, derived, or allowed to receive a **New Leaf Category Request**.
- A **New Leaf Category Request** must provide an allowed **Parent/Section Row** and a unique **Leaf Category Row** label.
- A reviewed second run registers a valid **New Leaf Category Request** in memory before planning workbook structure changes; the **Category Registry** file gains it only with the **Atomic Month Commit** (issue #19).
- The **Trust Policy** decides one **Authority** per row; workbook cells derive from row **Authority** (ADR 0001).
- Every category model is a **Suggester**; **Consensus** is the **Suggester** whose agreeing votes can earn `auto` under the **Trust Policy** (ADR 0002).
- The **Exception Sheet** lists every `review` row; the **Atomic Month Commit** writes nothing until it is empty (ADR 0003).
- A **Guidance Alias** matches after `human` **Category Memory** and before trusted `auto` **Category Memory** (ADR 0004).
- **Hosted Judgment** is deferred and not enabled; it would be a **Suggester** adapter and needs its own ADR and opt-in before use (ADR 0005).
- A **Confirmed Review Decision** can create or update **Category Memory**.
- Rule: Category Memory can learn only Leaf Category Row targets that exist in the Category Registry.
- Consensus results are learned as `auto` **Category Memory** that categorises only after two consistent committed months; before that it is a **Suggester** hint.
- **Category Memory** is generated private data and remains separate from a hand-written **Local Rule**.
- **Category Memory** uses **Merchant Identity** as its default matching key.
- A recurring **Confirmed Review Decision** can add a **Recurring Match Hint** to narrow future matches.
- A single **Confirmed Review Decision** can make future matching **Category Memory** review-free, but it does not bypass workbook safety checks.
- Committing a month learns its **Confirmed Review Decision** records into **Category Memory**; a **Reviewed Decision File** import remains a manual escape hatch.
- A dry run never writes **Category Memory**.
- A **Bank Statement** can support **Cashflow Row** updates.
- A **Bank Statement** can support **Net Salary Income** when a deterministic salary match exists.
- **Net Salary Income** may update the `Full-time job (net)` row when workbook safety checks pass.
- A **Salary Multi-Match** should be summed for reporting but remain review-only before writing.
- **Payroll Deduction Row** values must not be inferred from **Net Salary Income** alone.
- Existing workbook formulas or manual workbook logic for **Payroll Deduction Row** values should be preserved.
- `Income (net)` is a **Derived Workbook Row** and must not be directly written by the updater.
- Section totals such as `Cashflow`, `Assets`, `Investments`, `Living expenses`, `Services`, and `Total net worth` are **Derived Workbook Row** values and must not be directly written.
- The updater should write only **Leaf Workbook Row** values backed by source evidence.
- An **Investment Statement** can support **Asset Value Row** updates.
- A transfer shown on a **Bank Statement** is cash movement, not proof of an **Asset Value Row**.
- A **Month-End Market Value** updates an **Asset Value Row**.
- A **Holding Value** can update a matching individual **Asset Value Row**.
- A **Portfolio Total Value** can update only a mapped total row, not guessed individual holding rows.
- A **Digital Asset Value** is out of scope until a dedicated valuation source exists.
- A USD **Month-End Market Value** is converted to DKK with a **Fixed Conversion Rate** before it can update an **Asset Value Row**.
- An **Applied Conversion Rate** must be recorded in reports and audits for reproducibility.
- An **Applied Conversion Rate** is not written into the **Tracker Workbook** unless the workbook structure is explicitly changed later.
- An **Investment Contribution** updates a **Cashflow Row** when the tracker has a matching category.
- An **Internal Transfer** is excluded from generic income and expense totals unless deliberately mapped to a specific **Cashflow Row**.
- A **Credit Card Settlement** affects liability tracking and is not an expense.
- A **Card Purchase** can support expense categorization if an itemized card statement is ingested.
- A **Monthly Planning Run** can combine a **Bank Statement** and an **Investment Statement** for the same **Reporting Month**.
- A **Cross-Source Mismatch** is reported for review and does not let one source override another outside its evidence type.

## Example dialogue

> **Dev:** "Should a May refund adjust the April purchase it relates to?"
> **Domain expert:** "No. The updater records statement-driven monthly cashflow in the reporting month where the transaction appears."

> **Dev:** "A refund appears in the same month as the expense. Should it reduce the category?"
> **Domain expert:** "Yes, if the refund has a deterministic category match. Otherwise report it for review."

> **Dev:** "A June refund relates to an April purchase. Should April be changed?"
> **Domain expert:** "No. Record the refund in June if it has a deterministic category match."

> **Dev:** "Should reimbursements create a separate offset model?"
> **Domain expert:** "No. Keep the workbook structure; use Expense claims only when the claim is deterministically identified."

> **Dev:** "If I run the tool on June 1, should it always update May?"
> **Domain expert:** "Not in MVP 1. The run updates the explicit reporting month I choose."

> **Dev:** "The statement total for Food is 1,200 DKK, but the workbook already says 1,150 DKK. Should I overwrite it?"
> **Domain expert:** "No. Keep the workbook value and report the 1,200 DKK statement total for review."

> **Dev:** "The workbook already has rent filled in, and the bank statement confirms the payment. Should I write anything?"
> **Domain expert:** "No. Leave the pre-filled value alone and treat the statement as confirmation."

> **Dev:** "The merchant text says APPLE. Should I write it to Apple Cloud?"
> **Domain expert:** "Only if a deterministic rule says so. Otherwise report it for review."

> **Dev:** "I reviewed an unmatched merchant and assigned it to Food. Should future runs remember that?"
> **Domain expert:** "Yes. Learn from my confirmed review decision, but not from an unreviewed guess."

> **Dev:** "Should the learned merchant mapping be written into my local rules file?"
> **Domain expert:** "No. Keep learned category memory separate from hand-written local rules."

> **Dev:** "Should learned memory store the full transaction text with reference numbers?"
> **Domain expert:** "No. Store a normalized merchant identity, and add amount/date hints only when the payment is recurring."

> **Dev:** "Do I need to confirm the same merchant several times before it is trusted?"
> **Domain expert:** "No. One confirmed review decision is enough for future categorization, but writing still needs normal workbook safety checks."

> **Dev:** "Should the monthly run ask me questions interactively?"
> **Domain expert:** "No. Produce review output first, then import my reviewed decision file into category memory."

> **Dev:** "Can I import reviewed decisions and commit workbook changes in one command?"
> **Domain expert:** "No. Import decisions, dry-run again, then commit the workbook update after reviewing the result."

> **Dev:** "Should the investment statement be processed in a separate monthly workflow?"
> **Domain expert:** "No. Keep the source contracts separate, but combine their evidence into one monthly planning run."

> **Dev:** "Nordea shows 5,000 DKK transferred, but the investment statement shows 4,000 DKK deposited. Which wins?"
> **Domain expert:** "Neither overrides the other. Use each for its own evidence type and report the mismatch for review."

> **Dev:** "The bank statement shows a transfer to the broker. Should that update JEPI?"
> **Domain expert:** "No. That proves cash moved to investing. JEPI should come from an investment statement or another asset value source."

> **Dev:** "I contributed 5,000 DKK, but the investment is worth 4,850 DKK at month-end. Which value goes in the asset row?"
> **Domain expert:** "Use 4,850 DKK for the asset row. The 5,000 DKK contribution is separate cashflow."

> **Dev:** "The investment statement reports USD, but the tracker is DKK. Should the tool fetch live exchange rates?"
> **Domain expert:** "No. Use my configured fixed conversion rate and show the rate in the report."

> **Dev:** "If I change the fixed rate later, how do I know which rate May used?"
> **Domain expert:** "The May report and audit should record the applied conversion rate."

> **Dev:** "Should the workbook store the USD-to-DKK rate used?"
> **Domain expert:** "Not for now. Write the converted DKK value to the workbook and keep the rate in report/audit outputs."

> **Dev:** "Can commit mode add a missing month without telling me first?"
> **Domain expert:** "No. Dry-run should show the planned structure change before commit creates it."

> **Dev:** "Where should a new month column get formulas and formatting from?"
> **Domain expert:** "Copy the immediately previous period column and report which source column is used."

> **Dev:** "If the next year is missing, should the updater create only January?"
> **Domain expert:** "No. Create the full 12-month year block when the workbook pattern is clear."

> **Dev:** "Should last month's actual values be copied into a new month?"
> **Domain expert:** "No. Copy structure and formulas, but clear ordinary manual values."

> **Dev:** "Can the writer carry forward fixed subscription values when creating new months?"
> **Domain expert:** "Only for explicitly configured carry-forward recurring rows."

> **Dev:** "Can we reuse fixed rows as the carry-forward list?"
> **Domain expert:** "No. Fixed rows protect against overwrites; carry-forward rows authorize retaining copied recurring values."

> **Dev:** "If a workbook label or assumption mentions another currency, what should it be?"
> **Domain expert:** "For this tracker, labels and assumptions should be corrected to DKK."

> **Dev:** "Should a monthly update run fix workbook labels while writing values?"
> **Domain expert:** "No. Label correction is a separate workbook cleanup task."

> **Dev:** "The investment statement only gives a total account value. Should I split it between JEPI and OXY?"
> **Domain expert:** "No. Use explicit holding values for individual rows, or map the total to a total row if one exists."

> **Dev:** "Can a bank transfer to a crypto platform update the CRYPTO row?"
> **Domain expert:** "No. Digital asset values need a dedicated valuation source."

> **Dev:** "A transfer from checking to savings appears on the bank statement. Is that spending?"
> **Domain expert:** "No. It is an internal transfer unless I map that movement to a specific tracker cashflow row."

> **Dev:** "The bank statement shows a payment to the credit card. Should I categorize it as shopping or food?"
> **Domain expert:** "No. That payment settles the credit card liability. Expense categories need itemized card purchases."

> **Dev:** "Can we split a net salary bank deposit into taxes and labour market contribution?"
> **Domain expert:** "No. The bank statement proves net salary income only; preserve the workbook's formula/manual payroll logic for deduction rows."

> **Dev:** "Can a matched salary deposit write to Full-time job (net)?"
> **Domain expert:** "Yes, if the target cell is safe to write. Derived payroll rows stay workbook-owned."

> **Dev:** "What if there are two salary-like deposits in one month?"
> **Domain expert:** "Sum them in the report, but require review before writing."

> **Dev:** "Should the updater write Income (net) directly?"
> **Domain expert:** "No. Income (net) is a derived workbook row."

> **Dev:** "Should the updater write Cashflow or Total net worth?"
> **Domain expert:** "No. Those are derived workbook rows. Write source-backed leaf rows and let the workbook calculate totals."

## Flagged ambiguities

- "tracker" can mean either the automation or the workbook; resolved terms are **Monthly Tracker Workbook Updater** for the automation and **Tracker Workbook** for the spreadsheet.
- "month" can mean the calendar month of execution or the period being updated; resolved term is **Reporting Month** for the selected year/month period.
- "calculated" does not mean authoritative; resolved rule is that a **Statement Total** is advisory when a **Manual Workbook Value** already exists.
- "statement" is overloaded; resolved terms are **Bank Statement** for cash movement and **Investment Statement** for holdings or asset values.
- "transfer" is not automatically an expense; resolved term is **Internal Transfer** when cash moves between owned accounts.
- "split transfer" means a **Proxy Split Transfer** only when one source transaction intentionally backs multiple category allocations.
- "fixed conversion rate" for a split transfer means a configured **Proxy Split Conversion Rate**, not a live or inferred rate.
- "credit card payment" means **Credit Card Settlement**, not the underlying **Card Purchase** expenses.
- "match" means a **Deterministic Category Match** when deciding whether an automatic write is allowed.
- "auto-learning" means creating **Category Memory** on commit; consensus-only entries stay untrusted `auto` hints until two committed months agree.
- "local rules" are manually curated **Local Rules**; generated **Category Memory** is a separate private store.
- "merchant" in category memory means **Merchant Identity**, not the raw full statement description.
- "review CSV" is raw output until the user confirms decisions; resolved term is **Reviewed Decision File** for importable decisions.
- "run" means a **Monthly Planning Run** when it produces proposed updates for a reporting month.
- "mismatch" across sources means **Cross-Source Mismatch**, not an automatic correction.
- "conversion rate" means a user-maintained **Fixed Conversion Rate**, not a live FX lookup.
- "rate used" means **Applied Conversion Rate** for the specific reporting month, not whatever the current config says later.
- "currency" in workbook context means **Tracker Currency** DKK, even when a source statement uses USD before conversion.
- "cleanup" means a **Workbook Cleanup Task**, not a monthly financial update.
