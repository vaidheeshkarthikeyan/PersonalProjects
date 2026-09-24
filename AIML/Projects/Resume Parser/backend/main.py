from fastapi import FastAPI

app = FastAPI(title="AI Resume Parser API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Resume Parser Backend!"}