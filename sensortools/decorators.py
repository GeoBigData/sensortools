class InputError(Exception):
    pass


def ingest_wkt(func):
    def wrapper(aoi):
        if not isinstance(aoi, str):
            raise InputError('Input into {} function must be a WKT string'.format(func.__name__))
        output = func(aoi)
        return output
    return wrapper


def ingest_latlon(func):
    def wrapper(lat, lon):
        try:
            lat, lon = map(float, [lat, lon])
        except ValueError:
            raise InputError('latitude and longitude must be numeric values')
        if lat < -90 or lat > 90:
            raise InputError('latitude must be between -90 and 90')
        if lon < -180 or lon > 180:
            raise InputError('longitude must be between -180 and 180')
        output = func(lat, lon)
        return output
    return wrapper
