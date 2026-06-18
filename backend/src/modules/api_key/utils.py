from random import choices
from string import ascii_uppercase, digits


def generate_new_api_key() -> str:
    return 'API_KEY_SAC_' + ''.join(choices(digits+ascii_uppercase, k=64))