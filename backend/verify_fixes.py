"""
Verify P0 Bug Fixes
"""
import sys
import os

print("=== P0 Bug Fix Verification ===\n")

# Verify 1: Check if get_db is correctly imported in products.py
print("Verify BUG-001: Database Connection Fix")
with open('app/api/products.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'from app.api.deps import get_db' in content:
        print("[OK] get_db imported from deps")
    else:
        print("[FAIL] get_db import missing")
    
    if 'def get_db() -> Session:' in content and 'pass' in content:
        print("[FAIL] Local get_db stub still exists")
    else:
        print("[OK] Local stub removed")

print()

# Verify 2: Check if conversation.py exists
print("Verify BUG-002: Conversation Model Creation")
if os.path.exists('app/models/conversation.py'):
    print("[OK] conversation.py file created")
    with open('app/models/conversation.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'class Conversation(BaseModel):' in content:
            print("[OK] Conversation model defined")
        if 'class AgentType(enum.Enum):' in content:
            print("[OK] AgentType enum defined")
        if 'class ConversationStatus(enum.Enum):' in content:
            print("[OK] ConversationStatus enum defined")
        if 'class ContentType(enum.Enum):' in content:
            print("[OK] ContentType enum defined")
else:
    print("[FAIL] conversation.py file not found")

print()

# Verify 3: Check models/__init__.py
print("Verify BUG-002: Model Import Updates")
with open('app/models/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'from .conversation import Conversation, AgentType, ConversationStatus, ContentType' in content:
        print("[OK] Conversation models imported in __init__.py")
    else:
        print("[FAIL] Conversation import missing")

print()

# Verify 4: Check main.py router registration
print("Verify BUG-002: Product Router Registration")
with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'from app.api import products' in content:
        print("[OK] products module imported")
    else:
        print("[FAIL] products module not imported")
    
    if 'app.include_router' in content and 'products.router' in content:
        print("[OK] Product router registered")
    else:
        print("[FAIL] Product router not registered")

print()

# Verify 5: Check route paths
print("Verify Route Path Configuration")
with open('app/api/products.py', 'r', encoding='utf-8') as f:
    content = f.read()
    route_count = 0
    if '@router.get("/products"' in content:
        print("[OK] Product list route defined")
        route_count += 1
    if '@router.get("/products/{product_id}"' in content:
        print("[OK] Product detail route defined")
        route_count += 1
    if '@router.post("/products"' in content:
        print("[OK] Create product route defined")
        route_count += 1
    if '@router.put("/products/{product_id}"' in content:
        print("[OK] Update product route defined")
        route_count += 1
    if '@router.delete("/products/{product_id}"' in content:
        print("[OK] Delete product route defined")
        route_count += 1
    if '@router.get("/products/{product_id}/cultural-info"' in content:
        print("[OK] Cultural info route defined")
        route_count += 1
    if '@router.get("/products/categories/list"' in content:
        print("[OK] Categories route defined")
        route_count += 1
    if '@router.get("/products/regions/list"' in content:
        print("[OK] Regions route defined")
        route_count += 1
    if '@router.get("/products/statistics"' in content:
        print("[OK] Statistics route defined")
        route_count += 1
    
    print(f"\nTotal routes defined: {route_count}")

print()
print("=== Verification Complete ===")
