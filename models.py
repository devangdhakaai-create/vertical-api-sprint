from sqlalchemy import Column, Integer, String, Boolean
from database import Base
from pgvector.sqlalchemy import Vector

class TodoDB(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(384)) 
    source = Column(String, nullable=True)  # Optional source field to store the source of the chunk
    
# Vector(384) = 384-dimensional vector store karega — ye number tumhare embedding model pe depend karta hai (Week 2 mein sentence-transformers ka ek common model 384 dimensions deta hai — agar model badla to ye number bhi badlega)