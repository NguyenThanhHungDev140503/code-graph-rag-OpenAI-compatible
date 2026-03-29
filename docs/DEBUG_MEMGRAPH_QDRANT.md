# Hướng Dẫn Truy Cập Memgraph và Qdrant Để Debug

Tài liệu này hướng dẫn cách truy cập trực tiếp vào Memgraph (graph database) và Qdrant (vector store) để debug và phân tích data.

## Mục Lục

1. [Kết Nối Memgraph](#1-kết-nối-memgraph)
2. [Kết Nối Qdrant](#2-kết-nối-qdrant)
3. [Các Query Hữu Ích](#3-các-query-hữu-ích)
4. [Scripts Mẫu](#4-scripts-mẫu)

---

## 1. Kết Nối Memgraph

### Sử Dụng Python

```python
import mgclient

# Kết nối đến Memgraph
conn = mgclient.connect(host='localhost', port=7687)
conn.autocommit = True
cursor = conn.cursor()

# Test connection
cursor.execute("RETURN 1 AS test")
print(cursor.fetchone()[0])  # Output: 1
```

### Kiểm Tra Container Đang Chạy

```bash
docker ps | grep memgraph
```

Output mẫu:
```
cf0cbe94f354   code-graph-rag-memgraph   "/usr/local/bin/memg…"   Up 21 hours   0.0.0.0:7444->7444/tcp, 0.0.0.0:7687->7687/tcp
```

---

## 2. Kết Nối Qdrant

### Sử Dụng Python

```python
from qdrant_client import QdrantClient
from codebase_rag.config import settings

# Kết nối đến Qdrant
client = QdrantClient(host='localhost', port=6333)

# Lấy thông tin collection
info = client.get_collection('code_embeddings')
print(f"Points: {info.points_count}")
print(f"Status: {info.status}")
```

### Kiểm Tra Container

```bash
docker ps | grep qdrant
```

---

## 3. Các Query Hữu Ích

### 3.1. Thống Kê Tổng Quan Graph

```python
# Node counts by label
cursor.execute("""
MATCH (n)
RETURN labels(n)[0] as label, count(*) as count
ORDER BY count DESC
""")
print("Nodes:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")
```

**Output mẫu:**
```
Function: 2233
Module: 2167
UnresolvedFunction: 1916
File: 1855
Method: 1165
Class: 906
Folder: 669
StdlibMethod: 445
ExternalPackage: 152
Interface: 136
Enum: 21
StdlibClass: 7
Project: 1
```

### 3.2. Thống Kê CALLS Relationships

```python
# CALLS relationships by target type
cursor.execute("""
MATCH (caller)-[r:CALLS]->(target)
RETURN
    CASE
        WHEN target:Function THEN 'Function'
        WHEN target:Method THEN 'Method'
        WHEN target:StdlibMethod THEN 'StdlibMethod'
        WHEN target:UnresolvedFunction THEN 'UnresolvedFunction'
        ELSE 'Other'
    END as target_type,
    count(*) as count
ORDER BY count DESC
""")
print("CALLS by target type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")
```

**Output mẫu:**
```
StdlibMethod: 4336
UnresolvedFunction: 3368
Method: 146
Function: 47
```

### 3.3. Tính Resolution Rate

```python
cursor.execute("""
MATCH (caller)-[r:CALLS]->(target)
RETURN
    count(r) as total_calls,
    count(CASE WHEN target:Function THEN 1 END) as function_calls,
    count(CASE WHEN target:Method THEN 1 END) as method_calls,
    count(CASE WHEN target:StdlibMethod THEN 1 END) as stdlib_calls,
    count(CASE WHEN target:UnresolvedFunction THEN 1 END) as unresolved_calls
""")
row = cursor.fetchone()

total = row[0]
resolved = row[1] + row[2] + row[3]
resolution_rate = (resolved / total * 100) if total > 0 else 0

print(f"Total CALLS: {total}")
print(f"Resolved: {resolved} ({resolution_rate:.1f}%)")
print(f"Unresolved: {row[4]}")
```

### 3.4. Kiểm Tra Failed Relationships

```python
# Kiểm tra relationships với target NULL
cursor.execute("""
MATCH (caller)-[r:CALLS]->(target)
WITH caller, r, target
WHERE target IS NULL
RETURN count(DISTINCT r) as failed_count
""")
print(f"Failed relationships: {cursor.fetchone()[0]}")
```

### 3.5. Tìm Nodes Cụ Thể

```python
# Tìm tất cả StdlibMethod nodes
cursor.execute("""
MATCH (n:StdlibMethod)
RETURN n.qualified_name as name, n.library as library
ORDER BY name
LIMIT 20
""")
print("StdlibMethods:")
for row in cursor.fetchall():
    print(f"  {row[0]} (library: {row[1]})")
```

```python
# Tìm top unresolved functions
cursor.execute("""
MATCH (n:UnresolvedFunction)
RETURN n.qualified_name as name, count(*) as call_count
ORDER BY call_count DESC
LIMIT 20
""")
print("Top Unresolved:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} calls")
```

### 3.6. Query Embeddings Nodes

```python
from codebase_rag import constants as cs

# Sử dụng query từ constants.py
cursor.execute(cs.CYPHER_QUERY_EMBEDDINGS, {'project_prefix': 'tmpljj0iunw.'})
results = cursor.fetchall()

print(f"Total nodes for embeddings: {len(results)}")
for row in results[:5]:
    print(f"  {row}")
```

### 3.7. Kiểm Tra Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition

client = QdrantClient(host='localhost', port=6333)

# Lấy collection info
info = client.get_collection('code_embeddings')
print(f"Points: {info.points_count}")
print(f"Status: {info.status}")

# Scroll qua một số points
results = client.scroll(
    collection_name='code_embeddings',
    limit=10,
    with_vectors=False
)
print(f"\nSample points: {len(results[0])}")
for point in results[0]:
    print(f"  ID: {point.id}, Payload: {point.payload}")
```

---

## 4. Scripts Mẫu

### 4.1. Script Debug Full Summary

```python
#!/usr/bin/env python3
"""Debug script - Get full graph summary."""
import mgclient

def main():
    conn = mgclient.connect(host='localhost', port=7687)
    conn.autocommit = True
    cursor = conn.cursor()

    print("=" * 50)
    print("GRAPH SUMMARY")
    print("=" * 50)

    # 1. Node counts
    print("\n📍 Nodes by label:")
    cursor.execute("""
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # 2. Relationship counts
    print("\n🔗 Relationships by type:")
    cursor.execute("""
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(*) as count
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # 3. CALLS breakdown
    print("\n📞 CALLS resolution:")
    cursor.execute("""
        MATCH (caller)-[r:CALLS]->(target)
        RETURN
            CASE
                WHEN target:Function THEN 'Function'
                WHEN target:Method THEN 'Method'
                WHEN target:StdlibMethod THEN 'StdlibMethod'
                ELSE 'UnresolvedFunction'
            END as type,
            count(*) as count
        ORDER BY count DESC
    """)
    total = 0
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
        total += row[1]

    resolved = total - cursor.fetchone()[1] if total > 0 else 0
    print(f"\n  Resolution rate: {(resolved/total*100):.1f}%")

    conn.close()

if __name__ == "__main__":
    main()
```

Chạy:
```bash
uv run python debug_summary.py
```

### 4.2. Script Kiểm Tra Resolution Rate

```python
#!/usr/bin/env python3
"""Check resolution rate."""
import mgclient
from collections import Counter

conn = mgclient.connect(host='localhost', port=7687)
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("MATCH (caller)-[r:CALLS]->(target) RETURN count(r) as total")
total = cursor.fetchone()[0]

cursor.execute("""
    MATCH (caller)-[r:CALLS]->(target)
    RETURN labels(target)[0] as target_type, count(*) as count
""")

breakdown = dict(cursor.fetchall())
resolved = sum(v for k, v in breakdown.items() if k != 'UnresolvedFunction')
unresolved = breakdown.get('UnresolvedFunction', 0)

print(f"Total CALLS: {total}")
print(f"Resolved: {resolved} ({(resolved/total*100):.1f}%)")
print(f"Unresolved: {unresolved} ({(unresolved/total*100):.1f}%)")
```

### 4.3. Script Tìm Top Unresolved Functions

```python
#!/usr/bin/env python3
"""Find top unresolved functions."""
import mgclient

conn = mgclient.connect(host='localhost', port=7687)
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
    MATCH (n:UnresolvedFunction)
    RETURN n.qualified_name as name
    ORDER BY name
    LIMIT 50
""")

print("Sample Unresolved Functions:")
for i, row in enumerate(cursor.fetchall(), 1):
    print(f"{i}. {row[0]}")
```

---

## 5. Tham Khảo

### Connection Parameters

| Service | Host | Port |
|---------|------|------|
| Memgraph | localhost | 7687 |
| Qdrant | localhost | 6333 |

### Cấu Hình Trong Code

Xem `codebase_rag/config.py`:

```python
# Memgraph
MEMGRAPH_HOST = "localhost"
MEMGRAPH_PORT = 7687

# Qdrant
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
```

### Cypher Query Embeddings

Xem `codebase_rag/constants.py` - `CYPHER_QUERY_EMBEDDINGS`:

```python
CYPHER_QUERY_EMBEDDINGS = """
MATCH (m:Module)-[:DEFINES]->(n:Function)
WHERE m.qualified_name STARTS WITH $project_prefix
RETURN id(n) AS node_id, n.qualified_name AS qualified_name, ...

UNION ALL

MATCH (n:UnresolvedFunction)
RETURN ...
"""
```

---

**Lưu ý:** Thay đổi `project_prefix` ('tmpljj0iunw.') tùy theo project bạn đang debug.
