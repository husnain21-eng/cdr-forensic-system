# Changelog

All notable changes to the CDR Forensic Investigator System will be
documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-10-16

### Added

**Core security**
- AES (Fernet) encryption of the workspace database
- Master key stored in the OS keyring (Windows Credential Locker /
  macOS Keychain / Linux Secret Service)
- PBKDF2-HMAC-SHA256 password hashing with 200,000 iterations
- Role-Based Access Control (Admin, Junior Analyst) with enforced
  permissions
- HMAC-signed audit trail with hash chaining for tamper detection
- Secure file shredding — temp files overwritten 3x before deletion
- Brute-force protection — 5 failed attempts locks the account for
  5 minutes
- Strong password policy (10+ chars, upper, lower, digit, symbol)
- Idle auto-lock after 5 minutes of inactivity

**Data ingestion**
- Multi-format loader: CSV, XLSX, XLS with encoding fallback
- Automatic column normalization (A-Party, Caller, Source -> party_a)
- Coordinate extraction from cell-tower strings (6 formats supported)
- Bulk file loading with progress bar
- Support for Target A and Target B (for mutual analysis)

**Analysis**
- Contact network graph with centrality ranking (top 40 nodes)
- Transparent, documented risk scoring heuristic
- Anomaly detection: short calls (<= 5s), night activity (23:00-05:00)
- Mutual contact analysis between two targets
- Co-location detection via KDTree (time + distance)

**Visualization**
- 7-tab dashboard with horizontal tab bar navigation
- Interactive Folium map with marker clustering
- Cell tower frequency table
- Bar chart of top interlocutors
- Network graph with weighted edges

**Reporting**
- A4 PDF dossier with diagonal watermark and confidentiality header
- Print preview dialog for any tab (Ctrl+P)
- CSV export from any data table
- HMAC chain verification button in the audit tab

**UX**
- Modern design system (palette, spacing, stylesheet)
- Light/dark theme toggle (persisted)
- Adjustable font size (11-22 px, persisted)
- Toast notifications for non-blocking feedback
- Empty states on every tab
- Keyboard shortcuts for all major actions
- Advanced filters (date/time range + phone number)
- Reset session with confirmation dialog
- Auto-fit to screen resolution on startup

### Changed
- Replaced `pd.datetime.now()` with `pd.Timestamp.now()` for
  pandas 2.0+ compatibility
- Migrated from CartoDB tiles to Esri (no API key required)
- Refactored from monolithic file to layered package structure

### Fixed
- Watermark now renders correctly (uses `onFirstPage` /
  `onLaterPages` hooks)
- WAL journal mode replaced with DELETE to prevent plaintext
  sidecar files
- Circular import between `main_window` and `login_dialog` resolved
  via deferred import
- Print orientation API (moved from `QPrinter` to `QPageLayout`)

### Security
- All Priority 1 items from the hardening plan implemented:
  - Secure shred
  - Hash-chained audit trail
  - Strong password policy
  - Pinned dependencies
- `pip-audit` installed for ongoing CVE scanning

---

## [Unreleased] — Future enhancements

- SQLCipher for transparent database encryption
- TPM-backed key storage (hardware security module)
- Two-factor authentication (TOTP)
- Password-derived key wrapping (beyond OS keyring)
- Screenshot / screen-recording prevention
- Encrypted workspace backups
- External SIEM log shipping
- Code signing for distribution
- Wavelet-based call-frequency analysis
- STIX / MISP export for threat intelligence sharing

---

## [0.1.0] — Pre-release development

Initial project scaffolding, environment setup, and phased development
across 12 phases:

- Phase 1: Environment setup
- Phase 2: Core layer (crypto, database, RBAC, audit)
- Phase 3: Data layer (loader, schema, analyzers)
- Phase 4: Reports and maps
- Phase 5: UI design system
- Phase 6: Reusable components
- Phase 7: Dialogs
- Phase 8: Tab pages
- Phase 9: Main window wiring
- Phase 10: Entry point
- Phase 11: Testing and debugging
- Phase 12: Polish and documentation