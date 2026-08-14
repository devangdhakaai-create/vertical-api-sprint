import os
from groq import Groq
from retrieve import retrieve_similar_chunks

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def generate_answer(query: str, top_k: int = 3):
    chunks = await retrieve_similar_chunks(query, top_k=top_k)
    context = "\n\n".join([chunk.content for chunk in chunks])
    
    prompt = f"""Answer the question based only on the context below. If the answer isn't in the context, say so.

Context:
{context}

Question: {query}

Answer:"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    return response.choices[0].message.content