import json
from fastapi import FastAPI, Request, HTTPException
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

class Story(BaseModel):
    story_id: str
    story_title: str
    story_text: str
    genre: str
    size: str
    demographic: dict
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
    app.state.db = await get_db()
    await app.state.db.execute('''
        DROP TABLE IF EXISTS stories;
        CREATE TABLE IF NOT EXISTS stories (
           story_id SERIAL PRIMARY KEY,
            story_title TEXT,
            story_text TEXT,
            genre TEXT,
            size TEXT,
            demographic JSONB,
            themes TEXT
        )
    ''')

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/story")
async def create_story(story: Story):
    
    query = """
        INSERT INTO stories (story_id, story_title, story_text, genre, size, demographic, themes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """
    await app.state.db.execute(query, story.story_id, story.story_title, story.story_text, story.genre, story.size, json.dumps(story.demographic), story.themes)
    return {"message": "Story created successfully"}

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
# Get a story by its ID
@app.get("/story/{story_id}")
async def get_story(story_id: str):
    row = await app.state.db.fetchrow("SELECT * FROM stories WHERE story_id = $1", story_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Story not found")
    story = dict(row)
    return story

# Delete a story by its ID
@app.delete("/story/{story_id}")
async def delete_story(story_id: str):
    result = await app.state.db.execute("DELETE FROM stories WHERE story_id = $1", story_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Story not found")
    return {"message": "Story deleted successfully"}

# delete all and reset the database
@app.delete("/stories")
async def delete_stories():
    result = await app.state.db.execute("DELETE FROM stories")
    return {"message": "All stories deleted successfully"}

# Update a story by its ID
@app.put("/story/{story_id}")
async def update_story(story_id: str, story: Story):
    # Validate input data here if necessary
    result = await app.state.db.execute('''
        UPDATE stories SET story_title = $1, story_text = $2, genre = $3, size = $4, demographic = $5, themes = $6 WHERE story_id = $7
    ''', story.story_title, story.story_text, story.genre, story.size, story.demographic, story.themes, story_id)
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Story not found")
    return {"message": "Story updated successfully"}
