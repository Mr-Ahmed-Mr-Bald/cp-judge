import json, sys, time

def emit(data):
    print(json.dumps(data), flush=True)

emit({"event": "compiling"})
time.sleep(0.1)
emit({"event": "running", "test": 0})
time.sleep(0.1)
emit({"event": "running", "test": 1})
time.sleep(0.1)
emit({"event": "done", "verdict": "AC"})
sys.exit(0)
