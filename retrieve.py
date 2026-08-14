from dotenv import load_dotenv
load_dotenv()
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from models import DocumentChunk
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Query embedding generate karo aur similarity search likho

async def retrieve_similar_chunks(query: str, top_k: int = 5):
    query_embedding = model.encode(query).tolist()
    
    async with SessionLocal() as session:
        result = await session.execute(
            select(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        chunks = result.scalars().all()
        return chunks
    
# model.encode(query) = query ko bhi wahi embedding model se convert karo (same model use karna zaroori hai jo ingestion mein use kiya tha, warna vectors compatible nahi honge)
# .cosine_distance(query_embedding) = pgvector ka built-in operator hai jo cosine distance calculate karta hai (kam distance = zyada similar)
# .order_by(...) = sabse similar chunks pehle aayenge
# .limit(top_k) = sirf top 5 (default) results lo

# Test script
async def main():
    query = "What is Cloud Computing & What are the future opportunities in this field?"  # apne document ke topic se related question daalo
    results = await retrieve_similar_chunks(query, top_k=3)
    
    print(f"Query: {query}\n")
    for i, chunk in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(chunk.content[:300])  # pehle 300 characters dikhao
        print()

if __name__ == "__main__":
    asyncio.run(main())