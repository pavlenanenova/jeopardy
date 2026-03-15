import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.question import router as question_router
from app.api.routes.answer import router as answer_router
from app.api.routes.agent import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    required = ["DATABASE_URL", "GEMINI_API_KEY"]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    yield


app = FastAPI(
    title="Jeopardy API",
    lifespan=lifespan,
    description=(
        "A REST API for playing Jeopardy trivia.\n\n"
        "## How it works\n\n"
        "In Jeopardy the format is reversed from a normal quiz — you are given a clue and must "
        "respond with the correct answer. The `question` field in responses is the clue shown on "
        "the board, and the `answer` is what the contestant says.\n\n"
        "## Typical flow\n\n"
        "1. Call **GET /question/** to get a random clue\n"
        "2. Call **POST /verify-answer/** with your answer and the `question_id` to check if you're correct\n"
        "3. Or call **POST /agent-play/** to let an AI agent attempt a question autonomously"
    ),
    version="1.0.0",
)

app.include_router(question_router)
app.include_router(answer_router)
app.include_router(agent_router)