from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse 
from starlette.templating import Jinja2Templates
import asyncpg
from pydantic import BaseModel
import os

from dotenv import load_dotenv
load_dotenv()
app = FastAPI()

templates = Jinja2Templates(directory="templates")

app = FastAPI()

class Story(BaseModel):
    story_id: str
    story_text: str
    genre: str
    origin: str
    demographic: str
    themes: str

async def get_db():
   
    conn = await asyncpg.connect(
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
        host=os.getenv("DB_HOST")
    )
    return conn

@app.on_event("startup")
async def startup():
    print(os.getenv("DB_USERNAME"))
    app.state.db = await get_db()
    await app.state.db.execute('''
        CREATE TABLE IF NOT EXISTS stories
        (story_id TEXT, story_text TEXT, genre TEXT, origin TEXT, demographic TEXT, themes TEXT)
    ''')

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/story")
async def add_story(story: Story):
    await app.state.db.execute('''
        INSERT INTO stories VALUES ($1, $2, $3, $4, $5, $6)
    ''', story.story_id, story.story_text, story.genre, story.origin, story.demographic, story.themes)
    return {"message": "Story added successfully"}

@app.get("/stories")
async def get_stories():
    rows = await app.state.db.fetch("SELECT * FROM stories")
    stories = [dict(row) for row in rows]
    return {"stories": stories}