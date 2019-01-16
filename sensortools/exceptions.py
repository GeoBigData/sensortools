class MissingDUCAPIkeyError(Exception):
    """Raised when a ./duc-api.txt cannot be found"""
    pass


class DUCAPIkeyFormattingError(Exception):
    """Raised when DUC key cannot be extracted from ./duc-api.txt"""
    pass
