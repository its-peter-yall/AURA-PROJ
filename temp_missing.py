import json

with open('temp_models.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

models = data.get('data', [])

# Check if missing models are related to top_provider
top_providers = {}
for m in models:
    tp = m.get('top_provider', {})
    if tp:
        top_p = tp.get('context_length', 0) or 0
        if top_p not in top_providers:
            top_providers[top_p] = []
        top_providers[top_p].append(m['id'])

print('Top provider context_length distribution:')
for k, v in sorted(top_providers.items(), reverse=True)[:10]:
    print(f'  {k}: {len(v)}')

# Check models that are NOT in our API response
with open('temp_api_models.txt', 'r') as f:
    api_models = set(line.strip() for line in f if line.strip())

missing = [m['id'] for m in models if m['id'] not in api_models]
print(f'\nMissing from API ({len(missing)} total):')
for m in missing[:30]:
    print(f'  {m}')