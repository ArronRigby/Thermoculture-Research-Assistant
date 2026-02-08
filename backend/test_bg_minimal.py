from fastapi import FastAPI, BackgroundTasks
import asyncio
import uvicorn
import os

app = FastAPI()

async def back_task(name: str):
    with open("bg_test.log", "a") as f:
        f.write(f"STARTING BACKGROUND TASK: {name}\n")
    await asyncio.sleep(2)
    with open("bg_test.log", "a") as f:
        f.write(f"FINISHED BACKGROUND TASK: {name}\n")

@app.post("/test")
async def test_endpoint(background_tasks: BackgroundTasks):
    with open("bg_test.log", "a") as f:
        f.write("ENDPOINT CALLED\n")
    background_tasks.add_task(back_task, "TEST_JOB")
    return {"status": "ok"}

if __name__ == "__main__":
    if os.path.exists("bg_test.log"):
        os.remove("bg_test.log")
    uvicorn.run(app, host="127.0.0.1", port=8001)
