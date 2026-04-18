import sys, json

# Read from file
with open('temp_models.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

models = data.get('data', [])

# Get context_length for all models
context_lengths = {}
for m in models:
    cl = m.get('context_length', 0) or 0
    if cl not in context_lengths:
        context_lengths[cl] = 0
    context_lengths[cl] += 1

print('Context length distribution:')
for cl, cnt in sorted(context_lengths.items(), reverse=True)[:10]:
    print(f'  {cl}: {cnt}')

# Check if 0 context_length models are filtering
zero_context = [m['id'] for m in models if not m.get('context_length')]
print(f'Models with no context_length: {len(zero_context)}')

# Sample from missing vendors
missing_vendors = ['alibaba', 'baidu', 'cohere', 'amazon', 'inflection', 'microsoft', 'bytedance']
for v in missing_vendors:
    matching = [m['id'] for m in models if m['id'].startswith(v + '/')]
    print(f'{v}: {len(matching)} models')
    if matching:
        m = next(m for m in models if m['id'] == matching[0])
        print(f'  Example: {m["id"]}, context_length: {m.get("context_length")}')