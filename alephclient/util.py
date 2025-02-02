import os
import yaml
import time
import random
import logging
from banal import is_listish, is_mapping, ensure_list

try:
    from pathlib import Path  # noqa
except ImportError:
    from pathlib2 import Path  # noqa

log = logging.getLogger(__name__)


def backoff(err, failures):
    """Implement a random, growing delay between external service retries."""
    sleep = (2 ** max(1, failures)) + random.random()
    log.warning("Error: %s, back-off: %.2fs", err, sleep)
    time.sleep(sleep)


def load_config_file(file_path):
    """Load a YAML (or JSON) bulk load mapping file."""
    file_path = os.path.abspath(file_path)
    with open(file_path, 'r') as fh:
        data = yaml.safe_load(fh) or {}
    return resolve_includes(file_path, data)


def resolve_includes(file_path, data):
    """Handle include statements in the graph configuration file.

    This allows the YAML graph configuration to be broken into
    multiple smaller fragments that are easier to maintain."""
    if is_listish(data):
        return [resolve_includes(file_path, i) for i in data]
    if is_mapping(data):
        include_paths = ensure_list(data.pop('include', []))
        for include_path in include_paths:
            dir_prefix = os.path.dirname(file_path)
            include_path = os.path.join(dir_prefix, include_path)
            data.update(load_config_file(include_path))
        for key, value in data.items():
            data[key] = resolve_includes(file_path, value)
    return data
