import os
import multiprocessing

# Aleph client API settings
HOST = os.environ.get('MEMORIOUS_ALEPH_HOST')
HOST = os.environ.get('ALEPH_HOST', HOST)
HOST = os.environ.get('ALEPHCLIENT_HOST', HOST)

API_KEY = os.environ.get('MEMORIOUS_ALEPH_API_KEY')
API_KEY = os.environ.get('ALEPH_API_KEY', API_KEY)
API_KEY = os.environ.get('ALEPHCLIENT_API_KEY', API_KEY)

THREADS = int(os.environ.get('ALEPHCLIENT_THREADS', multiprocessing.cpu_count()))  # noqa
TIMEOUT = int(os.environ.get('ALEPHCLIENT_TIMEOUT', 15))
MAX_TRIES = int(os.environ.get('ALEPHCLIENT_MAX_TRIES', 5))
