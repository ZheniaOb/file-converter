from .rejestr import ConversionError, ConversionRequest, REGISTRY, available_targets, execute
from . import biuro, dane, dokumenty  # import rejestruje konwertery

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())  # logi tylko, gdy aplikacja je skonfiguruje
