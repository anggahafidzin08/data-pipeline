class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DatabaseError(PipelineError):
    """Database operation failed."""
    pass

class ValidationError(PipelineError):
    """Data validation failed."""
    pass

class ConfigurationError(PipelineError):
    """Configuration is missing or invalid."""
    pass
