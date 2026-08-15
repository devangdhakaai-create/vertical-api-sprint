from dotenv import load_dotenv
load_dotenv()
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from models import DocumentChunk
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder

model = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Query embedding generate karo aur similarity search likho

async def retrieve_similar_chunks(query: str, top_k: int = 5, rerank: bool = False, candidate_pool: int = 15):
    query_embedding = model.encode(query).tolist()
    
    fetch_count = candidate_pool if rerank else top_k
    
    async with SessionLocal() as session:
        result = await session.execute(
            select(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(fetch_count)
        )
        chunks = result.scalars().all()
    
    if rerank:
        chunks = rerank_chunks(query, chunks, top_k=top_k)
    
    return chunks
# Logic: agar re-ranking chahiye, to pehle zyada candidates lo (jaise 15), phir unme se best top_k (jaise 3) cross-encoder se chuno — do-stage retrieval
# model.encode(query) = query ko bhi wahi embedding model se convert karo (same model use karna zaroori hai jo ingestion mein use kiya tha, warna vectors compatible nahi honge)
# .cosine_distance(query_embedding) = pgvector ka built-in operator hai jo cosine distance calculate karta hai (kam distance = zyada similar)
# .order_by(...) = sabse similar chunks pehle aayenge
# .limit(top_k) = sirf top 5 (default) results lo

def rerank_chunks(query:str,chunks:list,top_k:int=3) -> list:
    pairs = [[query, chunk.content] for chunk in chunks]
    scores = reranker.predict(pairs)
    
    scored_chunks = list(zip(chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    return [chunk for chunk, score in scored_chunks[:top_k]]
# pairs = har chunk ko query ke saath pair banate hain (cross-encoder ka input format yehi hota hai)
# reranker.predict(pairs) = har pair ko ek relevance score deta hai
# sort(..., reverse=True) = highest score wale pehle
# [:top_k] = sirf best top_k return karo

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