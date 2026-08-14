import pymupdf # Ye ek library hai jo PDF aur image files ko manipulate karne ke liye use hoti hai. Iska use karke aap PDF files ko read, write, aur modify kar sakte hain.
from sentence_transformers import SentenceTransformer
from models import DocumentChunk
import asyncio
from database import SessionLocal

def extract_text_from_pdf(pdf_path:str) -> str:
    doc = pymupdf.open(pdf_path)  # PDF file ko open karna
    full_text = ""
    for page in doc:  # Har page ke liye loop
        full_text += page.get_text()  # Page se text extract karna
    doc.close()  # PDF file ko close karna
    return full_text  # Extracted text ko return karna

# fitz.open() = PDF kholta hai
# page.get_text() = us page ka plain text nikalta hai

# Chunking strategy #1 — Fixed-size chunking

def fixed_size_chunk(text:str, chunk_size:int=500,overlap: int=50)->list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
# chunk_size = 500 = har chunk 500 characters ka
# overlap = 50 = consecutive chunks 50 characters overlap karte hain (taaki sentence beech mein na kate, context thoda continue rahe)

# Chunking strategy #2 — Semantic chunking (paragraph-based)
def semantic_chunk(text: str, max_chunk_size: int = 500) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(para) > max_chunk_size:
            # Agar akela paragraph hi bahut bada hai, use fixed-size se todo
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            sub_chunks = fixed_size_chunk(para, chunk_size=max_chunk_size, overlap=50)
            chunks.extend(sub_chunks)
        elif len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks
# Embedding model load karo

model = SentenceTransformer('all-MiniLM-L6-v2') # ye 384-dimension embeddings deta hai
# Ye pehli baar chalega to model download hoga (~80MB), thoda time lega

# Embeddings generate karo
def generate_embeddings(chunks:list[str])->list:
    embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
    return embeddings

async def store_chunks(chunks: list[str], embeddings, source:str):
    async with SessionLocal() as session:
        for chunk_text, embedding in zip(chunks, embeddings):
            new_chunk = DocumentChunk(
                content=chunk_text,
                embedding=embedding.tolist(), #numpy array ko Python list mein convert karna zaroori hai, kyunki pgvector column ko list chahiye
                source=source
            )
            session.add(new_chunk)
        await session.commit()
        print(f"stored {len(chunks)} chunks from {source}")
        
# zip(chunks, embeddings) = dono lists ko paired tarike se loop karta hai (chunk 1 ke saath embedding 1, chunk 2 ke saath embedding 2, ...)
# embedding.tolist() = sentence-transformers numpy arrays deta hai, lekin pgvector column ko Python list chahiye — conversion zaroori hai

# Test script — sab kuch chain karo

# if __name__ == "__main__":
#     text = extract_text_from_pdf("data/your_file.pdf")
    
#     fixed_chunks = fixed_size_chunk(text)
#     semantic_chunks = semantic_chunk(text)
    
#     print(f"Fixed-size chunking: {len(fixed_chunks)} chunks")
#     print(f"semantic chunking: {len(semantic_chunks)} chunks")
    
#     print("\n--- Sample fixed chunk ---")
#     print(fixed_chunks[0])
    
#     print("\n--- Sample semantic chunk ---")
#     print(semantic_chunks[0])
    
#     embeddings = generate_embeddings(fixed_chunks[:3])
#     print(f"\nEmbidding shape: {embeddings.shape}")

if __name__ == "__main__":
    pdf_path = "data/your_file.pdf"
    print("Starting extraction...")
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted text length: {len(text)}")
    
    chunks = semantic_chunk(text) # semantic chunk use karega as primary
    print(f"Total Chunks: {len(chunks)}")
    
    # chunks = chunks[:50] # sirf pehle 50 chunks ko test ke liye use karenge
    embeddings = generate_embeddings(chunks)
    print(f"Embeddings Generated: {embeddings.shape}")
    
    asyncio.run(store_chunks(chunks, embeddings, source=pdf_path))
    print("Done storing!")
    
# semantic_chunk ko primary chuna hai kyunki wo zyada meaningful boundaries deta hai — interview mein ye justify kar sakte ho ("fixed-size test kiya, lekin semantic chunks ne better context preserve kiya")