from pathlib import Path
import configparser
from json import loads

base = 'app/config'
config_files = [
    'environment.ini',
    'game_settings.ini'
]
config_paths = list(map(
    lambda file: Path(base) / Path(file),
    config_files
))

cfg = configparser.ConfigParser()
cfg.read(config_paths, encoding='utf-8')

section = 'game_money'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.getint(section, key), keys)
)))

section = 'table_specs'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: loads(cfg.get(section, key)), keys)
)))

section = 'database'
keys = cfg.options(section)
locals().update(dict(zip(
    map(lambda key: key.upper(), keys),
    map(lambda key: cfg.get(section, key), keys)
)))

