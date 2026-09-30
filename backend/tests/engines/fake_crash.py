import json, sys

print(json.dumps({"event": "compiling"}), flush=True)
print("Something went terribly wrong", file=sys.stderr)
sys.exit(1)
