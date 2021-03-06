# -*- coding: utf-8 -*-

__all__ = [
    'ValidationError',
    'FieldRequiredError',
    'TypeIsNotSupported',
    'DefaultValueError',
    'ImmutableDocumentError',
    'ImmutableFieldError',
    'ModelValidationError'
]


class ValidationError(Exception):
    """ Custom exception class. Useful for validation methods """

    def __str__(self):
        return self.message


class ModelNotFoundError(ValidationError):
    """Raises when DocumentField has wrong model assignment"""
    pass


class ModelValidationError(ValidationError):
    """User-defined exception. Raised when model validation is failed"""
    pass


class FieldError(ValidationError):
    """Field specific exception"""
    pass


class FieldRequiredError(FieldError):
    """ Raised when required field is not found """
    pass


class DefaultValueError(FieldError):
    """Raised when default value is wrong"""
    pass


class ImmutableDocumentError(ValidationError):
    """Raised when try to set any field in the immutable document"""
    pass


class ImmutableFieldError(FieldError):
    """Raised when try to set certain immutable field in a document"""
    pass
