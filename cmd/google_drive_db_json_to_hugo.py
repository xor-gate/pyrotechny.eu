#!/usr/bin/env python3
import json

import config
from urllib.request import urlopen

resp = urlopen(config.GOOGLE_DRIVE_EBOOK_LIBRRARY_DB_JSON_URL)
data = json.loads(resp.read())

print(data)
