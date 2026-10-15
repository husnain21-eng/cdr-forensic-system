"""Central constants — no magic numbers in business logic."""

# --- Crypto ---
PBKDF2_ITERATIONS = 200_000
PBKDF2_SALT_BYTES = 32
KEYRING_SERVICE = "cdr_forensic_system"
KEYRING_USER = "master_key"

# --- Auth ---
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
IDLE_TIMEOUT_SECONDS = 300

# --- Data ---
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
SHORT_CALL_THRESHOLD_SEC = 5
NIGHT_HOURS = (23, 0, 1, 2, 3, 4, 5)

# --- Roles ---
ROLE_ADMIN = "Senior Investigator / Admin"
ROLE_ANALYST = "Junior Analyst"
ROLES = (ROLE_ADMIN, ROLE_ANALYST)

# --- Permissions ---
PERM_LOAD_DATA = "load_data"
PERM_EXPORT_PDF = "export_pdf"
PERM_RESET_SESSION = "reset_session"
PERM_MANAGE_REGISTRY = "manage_registry"
PERM_VIEW_AUDIT = "view_audit"

ROLE_PERMISSIONS = {
    ROLE_ADMIN: {
        PERM_LOAD_DATA,
        PERM_EXPORT_PDF,
        PERM_RESET_SESSION,
        PERM_MANAGE_REGISTRY,
        PERM_VIEW_AUDIT,
    },
    ROLE_ANALYST: {
        PERM_LOAD_DATA,
        PERM_EXPORT_PDF,
    },
}