# Local dump sender module (temporary)
import json

import os

def dump(snapshot, log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")
