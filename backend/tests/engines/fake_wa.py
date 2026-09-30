import json, sys

def emit(data):
    print(json.dumps(data), flush=True)

emit({"event": "compiling"})
emit({"event": "running", "test": 0})
emit({"event": "running", "test": 1})
emit({"event": "done", "verdict": "WA", "test": 1})
sys.exit(0)
