"""Domain exceptions."""


class AppError(Exception):
    """Base application error."""


class ValidationError(AppError):
    """Raised when input or data validation fails."""


class NotFoundError(AppError):
    """Raised when a requested record cannot be found."""


class DuplicateError(AppError):
    """Raised when a unique value is duplicated."""


class PermissionError(AppError):
    """Raised when a user lacks a required permission."""


class DataIntegrityError(AppError):
    """Raised when CSV data fails integrity validation."""


class TransactionError(AppError):
    """Raised when a transaction cannot be safely completed."""


class InsufficientStockError(AppError):
    """Raised when a sale or adjustment would make stock negative."""


class ConcurrencyError(AppError):
    """Raised when a lock or transaction cannot be acquired."""