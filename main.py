from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional
from database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import TodoDB
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from logger import log
from dotenv import load_dotenv
from rag import generate_answer

load_dotenv()  # Load environment variables from .env file

def log_todo_creation(title: str):
    with open("log.txt", "a") as f:
        f.write(f"Todo created: {title}\n")

# Ye pattern dependency injection kehlata hai — FastAPI ka core feature
async def get_db():
    async with SessionLocal() as session:
        yield session # yield = FastAPI ko session deta hai, request khatam hone pe automatically close ho jata hai
        
app = FastAPI()

@app.get("/")
async def read_root():
    return {"status": "ok"}

class Todo(BaseModel): # Pydantic ka base class, isse inherit karke tum apna data shape define karte ho
    title: str = Field(...,min_length=1, max_length=100) # ... matlab required field hai, aur title 1-200 characters ke beech hona chahiye Agar koi empty title bheje (""), Pydantic khud reject karega 422 error ke saath
    completed: bool  = False # default value, agar client na bheje to False maan lega
# todos: list[Todo] = [] #In-memory storage banao (for temporary purpose)
    
@app.post("/todos", response_model=Todo)
# def create_todo(todo: Todo): #FastAPI automatically request body ko validate karega Todo model ke against
#     todos.append(todo)
#     return todo #Agar client galat data bheje (jaise id missing), FastAPI khud 422 error dega — tumhe manually check nahi karna
async def create_todo(todo: Todo, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    new_todo = TodoDB(title=todo.title, completed=todo.completed)  # id nahi diya
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    background_tasks.add_task(log_todo_creation, todo.title)
    log.info("todo_created", todo_id=new_todo.id, title=new_todo.title) #log.info("todo_created", ...) = ye structured log hai — event name + relevant fields, sirf plain text nahi
    return new_todo

# @app.get("/todos", response_model=list[Todo])
# def get_todos():
#     return todos

# @app.get("/todos/{todo_id}", response_model=Todo)
# def get_todo(todo_id: int):
#     for todo in todos:
#         if todo.id == todo_id:
#             return todo
#     raise HTTPException(status_code=404, detail="Todo Not Found") #proper error response bhejne ka FastAPI ka tarika

@app.get("/todos", response_model=list[Todo])
async def get_todos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TodoDB)) #select(TodoDB) = SQL query banata hai "SELECT * FROM todos"
    return result.scalars().all() #.scalars().all() = result ko Python objects ki list mein convert karta hai
    
@app.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    log.info("todo_deleted", todo_id=todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, updated_todo: Todo, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.title = updated_todo.title
    todo.completed = updated_todo.completed
    await db.commit()
    await db.refresh(todo)
    log.info("todo_updated", todo_id=todo_id, title=todo.title)
    return todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    await db.delete(todo)
    await db.commit()
    log.info("todo_deleted", todo_id=todo_id)
    return {"message": "Todo deleted"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
    

class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask_question(request: QueryRequest):
    answer = await generate_answer(request.query)
    return {"query": request.query, "answer": answer}