class MissingDUCAPIkeyError(Exception):
    """Raised when a ./duc-api.txt cannot be found"""
    pass


class DUCAPIError(Exception):
    """Raised when and error is returned from the DUC API"""
    pass
