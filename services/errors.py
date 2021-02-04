import json
from json.decoder import JSONDecodeError


def is_404_error(error):
    error_found = False
    try:
        if isinstance(error, str):
            error = json.loads(error)
        elif not isinstance(error, dict):
            raise ValueError('error must be either json string or json object(dict in python).')

        if error['error']['code'] == 404:
            error_found = True
    except (JSONDecodeError, KeyError):
        # error_found is initialized to False, so there's no need to set it here.
        pass

    return error_found
