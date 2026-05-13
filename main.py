from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Badiboss Pay API Running"}

@app.post("/serdipay/callback")
async def serdipay_callback(request: Request):
    data = await request.json()
    print("CALLBACK:", data)

    return {
        "success": True
    }
