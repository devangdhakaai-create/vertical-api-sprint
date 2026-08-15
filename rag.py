import os
from groq import Groq
from retrieve import retrieve_similar_chunks

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def generate_query_variations(query: str, n: int = 3) -> list[str]:
    prompt = f"""Generate {n} different ways to ask this same question, to help search a document more thoroughly. Return only the questions, one per line, no numbering.

Original question: {query}"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    variations = response.choices[0].message.content.strip().split("\n")
    variations = [v.strip() for v in variations if v.strip()]
    return variations
# temperature=0.7 = yaha thoda zyada creativity chahiye (variations diverse hone chahiye), isliye pehle wale RAG answer se zyada hai

async def multi_query_retrieve(query: str, top_k: int = 3) -> list:
    variations = await generate_query_variations(query)
    all_variations = [query] + variations  # original query bhi include karo
    
    seen_ids = set()
    merged_chunks = []
    
    for variant in all_variations:
        chunks = await retrieve_similar_chunks(variant, top_k=top_k)
        for chunk in chunks:
            if chunk.id not in seen_ids:
                seen_ids.add(chunk.id)
                merged_chunks.append(chunk)
    
    return merged_chunks

# seen_ids set = duplicate chunks avoid karta hai (agar do queries same chunk retrieve karein)
# Har variation se top_k chunks aate hain, sab merge hote hain unique list mein

async def generate_answer(query: str, top_k: int = 3, use_multi_query: bool = False, use_hyde: bool = False):
    if use_hyde:
        chunks = await hyde_retrieve(query, top_k=top_k)
    elif use_multi_query:
        chunks = await multi_query_retrieve(query, top_k=top_k)
    else:
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

# use_multi_query: bool = False = default single-query rahega (fast), lekin flag se multi-query switch kar sakte ho — ye interview mein achha point hai ("configurable retrieval strategy")

async def hyde_retrieve(query: str, top_k: int = 3) -> list:
    prompt = f"Write a short hypothetical paragraph answering this question: {query}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    
    hypothetical_answer = response.choices[0].message.content
    chunks = await retrieve_similar_chunks(hypothetical_answer, top_k=top_k)
    return chunks