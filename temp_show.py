import sys, json

response = sys.stdin.read()
data = json.loads(response)
or_models = [m for m in data if m['provider'] == 'openrouter']
print(f'OpenRouter models from API: {len(or_models)}')

# Show all model names
for m in or_models:
    print(f'  {m["name"]}')