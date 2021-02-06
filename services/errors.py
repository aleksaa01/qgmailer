import json
from json.decoder import JSONDecodeError


def get_error_code(error):
    error_code = None
    try:
        if isinstance(error, str):
            error = json.loads(error)
        elif not isinstance(error, dict):
            raise ValueError('error must be either json string or json object(dict in python).')

        error_code = error['error']['code']
    except (JSONDecodeError, KeyError):
        pass

    return error_code
