"""
Diagnostic script to check Celery Redis queues and worker status.
Run from project root with root venv activated.
"""
import sys
import os

# Ensure AURA-NOTES-MANAGER is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "AURA-NOTES-MANAGER"))

from api.config import REDIS_URL
from api.tasks.document_processing_tasks import app

print(f"Redis URL (from config): {REDIS_URL}")
print(f"Celery app name: {app.main}")
print(f"Celery broker: {app.conf.broker_url}")
print(f"Task routes: {app.conf.task_routes}")
print()

# Check Redis queues
import redis

r = redis.Redis.from_url(REDIS_URL)
try:
    print("Redis ping:", r.ping())
    print()
    
    # Check default celery queue
    celery_len = r.llen("celery")
    print(f"Queue 'celery' length: {celery_len}")
    
    # Check kg_processing queue
    kg_len = r.llen("kg_processing")
    print(f"Queue 'kg_processing' length: {kg_len}")
    
    # Show first few messages if any
    if kg_len > 0:
        msgs = r.lrange("kg_processing", 0, 2)
        print(f"First message in kg_processing (raw): {msgs[0][:200] if msgs else 'none'}...")
    if celery_len > 0:
        msgs = r.lrange("celery", 0, 2)
        print(f"First message in celery (raw): {msgs[0][:200] if msgs else 'none'}...")
        
except Exception as e:
    print(f"Redis error: {e}")

print()
# Try to inspect workers
print("Inspecting workers...")
try:
    inspector = app.control.inspect(timeout=5)
    active = inspector.active()
    registered = inspector.registered()
    stats = inspector.stats()
    
    if active:
        print(f"Active workers: {list(active.keys())}")
        for name, tasks in active.items():
            print(f"  {name}: {len(tasks)} active tasks")
    else:
        print("No active workers found (or inspect timed out).")
    
    if registered:
        for name, tasks in registered.items():
            print(f"  {name} registered tasks: {tasks}")
    else:
        print("No registered tasks found.")
        
    if stats:
        for name, s in stats.items():
            print(f"  {name} stats: {s}")
    else:
        print("No worker stats found.")
        
except Exception as e:
    print(f"Inspect error: {e}")
