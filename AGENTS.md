# AGENTS.md

Persistent project rules for this OpenCode workspace.

## Project

Integrated Cashier POS + Inventory Management System.

Python desktop application using CustomTkinter.

CSV files are the exclusive persistent business-data storage.

Never introduce SQLite or another database engine.

## Architecture Rules

- Keep UI, business logic, and storage separated.
- All persistent business data flows through repositories and services.
- Do not scatter raw CSV operations across UI callbacks.
- Use Decimal for monetary values.
- Preserve historical sale cost fields.
- Never hard-delete products or completed sales.
- Validate file integrity during startup.

## Data Integrity

- CSV is the only persistent business data store.
- Use the transaction coordinator for multi-file operations.
- Keep stock movements as the authoritative inventory ledger.
- Recover interrupted writes using transaction_journal.csv.
- Do not report success before persistence and verification.
- Prevent duplicate checkout submissions.

## Security

- Never store plaintext passwords.
- Enforce permissions in service functions, not only in the UI.
- CSV files can be read directly by filesystem users; document this limitation.

## Development

- Update PROJECT_STATUS.md after each completed phase.
- Run syntax checks and relevant tests before continuing.
- Prefer targeted changes over rewriting working modules.