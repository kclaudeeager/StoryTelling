from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse 
from starlette.templating import Jinja2Templates
import asyncpg
from pydantic import BaseModel
import os
import uuid

from dotenv import load_dotenv
load_dotenv()
app = FastAPI()

templates = Jinja2Templates(directory="templates")

app = FastAPI()

class Story(BaseModel):
    story_id: str
    story_text: str
    genre: str
    size: str
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
    story_id = str(uuid.uuid4())
    await app.state.db.execute('''
        INSERT INTO stories VALUES ($1, $2, $3, $4, $5, $6)
    ''', story_id, story.story_text, story.genre, story.size, story.demographic, story.themes)
    return {"message": "Story added successfully", "story_id": story_id}

@app.get("/stories-show", response_class=HTMLResponse)
async def get_stories(request: Request):
    rows = await app.state.db.fetch("SELECT * FROM stories")
    stories = [dict(row) for row in rows]
    # render the stories in the template using the storeis.html file
    return templates.TemplateResponse("stories.html", {"request": request, "stories": stories})

@app.get("/stories")
async def get_stories(request: Request):
    rows = await app.state.db.fetch("SELECT * FROM stories")
    stories = [dict(row) for row in rows]
    
    return stories
# add a route to get a single story by its id
@app.get("/story/{story_id}")
async def get_story(story_id: str):
    row = await app.state.db.fetchrow("SELECT * FROM stories WHERE story_id = $1", story_id)
    story = dict(row)
    return story
# add a route to delete a story by its id
@app.delete("/story/{story_id}")
async def delete_story(story_id: str):
    await app.state.db.execute("DELETE FROM stories WHERE story_id = $1", story_id)
    return {"message": "Story deleted successfully"}
# add a route to update a story by its id
@app.put("/story/{story_id}")
async def update_story(story_id: str, story: Story):
    await app.state.db.execute('''
        UPDATE stories SET story_text = $1, genre = $2, origin = $3, demographic = $4, themes = $5 WHERE story_id = $6
    ''', story.story_text, story.genre, story.size, story.demographic, story.themes, story_id)
    return {"message": "Story updated successfully"}

