import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.whatsapp import router as whatsapp_router
from app.api.dashboard import router as dashboard_router

# Initialize the FastAPI application
app = FastAPI(
    title="VESTA: Digital Didi Swarm",
    description="A multi-agent system for the safety and rights of informal workers.",
    version="1.0.0"
)

# Configure CORS (Essential for your dashboard to talk to the backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the routers from your app/api/ directory
app.include_router(whatsapp_router, prefix="/api/v1", tags=["Communication"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["Analytics"])

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "system": "VESTA Swarm",
        "message": "Monitoring the safety and rights of workers in West Bengal."
    }

if __name__ == "__main__":
    # To run the server: python app/main.py
    # This will start the FastAPI app on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)