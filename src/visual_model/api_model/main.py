from fastapi import FastAPI
from api.middleware.cors import add_cors
from api.api import router

app = FastAPI(
    title="GroundBit Visual Disease Detection",
    version="1.0.0"
)

add_cors(app)
app.include_router(router)