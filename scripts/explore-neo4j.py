#!/usr/bin/env python3
"""Simple script to explore Neo4j data without browser."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.retrieval import Retriever

def main():
    print("🔍 Exploring Neo4j Database")
    print("=" * 40)
    
    retriever = Retriever()
    
    try:
        with retriever.driver.session() as session:
            # Count nodes by type
            print("\n📊 Node Counts:")
            for label in ["Document", "Chunk", "Section"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"  {label}: {count}")
            
            # Show documents
            print("\n📄 Documents:")
            result = session.run("""
                MATCH (d:Document) 
                RETURN d.docId, d.filename, d.pageCount
            """)
            for record in result:
                print(f"  📄 {record['d.filename']} ({record['d.pageCount']} pages)")
                print(f"     ID: {record['d.docId']}")
            
            # Show sample chunks
            print("\n📝 Sample Chunks:")
            result = session.run("""
                MATCH (c:Chunk)
                RETURN c.chunkId, c.text, c.pageNum
                ORDER BY c.chunkIndex
                LIMIT 5
            """)
            for i, record in enumerate(result, 1):
                text = record["c.text"][:60] + "..." if len(record["c.text"]) > 60 else record["c.text"]
                print(f"  {i}. [{record['c.chunkId']}] Page {record['c.pageNum']}")
                print(f"     {text}")
            
            # Show sections
            print("\n🏷️  Sections:")
            result = session.run("""
                MATCH (s:Section)
                RETURN s.headings
                LIMIT 10
            """)
            for record in result:
                headings = " > ".join(record["s.headings"])
                print(f"  • {headings}")
            
            # Test search
            print("\n🔍 Test Search: 'Hermes'")
            result = session.run("""
                MATCH (c:Chunk)
                WHERE c.text CONTAINS 'Hermes'
                RETURN c.chunkId, c.text, c.pageNum
                LIMIT 3
            """)
            for record in result:
                text = record["c.text"][:80] + "..." if len(record["c.text"]) > 80 else record["c.text"]
                print(f"  📍 [{record['c.chunkId']}] Page {record['c.pageNum']}")
                print(f"     {text}")
    
    finally:
        retriever.close()
    
    print("\n" + "=" * 40)
    print("✅ Database exploration complete!")
    print("\n💡 To access Neo4j Browser:")
    print("   1. Open: http://localhost:7474")
    print("   2. Connect URL: bolt://localhost:7687")
    print("   3. Username: neo4j")
    print("   4. Password: your_secure_password")

if __name__ == "__main__":
    main()
