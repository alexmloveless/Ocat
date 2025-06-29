"""
Custom exception classes for Ocat application.

This module defines specific exception types for different error scenarios,
enabling better error handling and user feedback.
"""


class OcatError(Exception):
    """
    Base exception class for all Ocat-specific errors.

    This serves as the base class for all custom exceptions in the Ocat application,
    allowing for easy categorization and handling of application-specific errors.
    """

    pass


class ConfigError(OcatError):
    """
    Exception raised for configuration-related errors.

    This includes errors in configuration file parsing, validation failures,
    missing required configuration values, or invalid configuration parameters.
    """

    pass


class LLMError(OcatError):
    """
    Exception raised for LLM backend-related errors.

    This includes API communication failures, authentication errors,
    rate limit exceeded, model availability issues, or response parsing errors.
    """

    pass


class VectorStoreError(OcatError):
    """
    Exception raised for vector store operation errors.

    This includes database connection failures, index corruption,
    embedding generation errors, or search operation failures.
    """

    pass


class CommandError(OcatError):
    """
    Exception raised for slash command execution errors.

    This includes invalid command syntax, missing required parameters,
    file operation failures, or command execution errors.
    """

    pass


class PromptError(OcatError):
    """
    Exception raised for system prompt loading errors.

    This includes missing prompt files, invalid prompt syntax,
    or template rendering failures.
    """

    pass
