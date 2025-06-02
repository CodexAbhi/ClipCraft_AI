# main.py - Your FastAPI application for Render
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import requests
import json
import os
import time
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage (replace with database in production)
video_requests_db = {}

# Pydantic models for request/response validation
class VideoGenerationRequest(BaseModel):
    script_text: str = Field(..., min_length=1, max_length=5000, description="Text for the AI to speak (REQUIRED)")
    template_id: Optional[str] = Field(default=None, description="HeyGen template ID (optional)")
    use_captions: Optional[bool] = Field(default=False, description="Whether to enable captions")
    avatar_id: Optional[str] = Field(default="283a8bced1f841c7a9292a9212019165", description="Avatar character ID")
    voice_id: Optional[str] = Field(default="fc3a1b6d218246d39ff5199ab147d6ee", description="Voice ID")
    background_url: Optional[str] = Field(default="https://static.heygen.ai/tmp_resource/7fba946a-b927-4bc9-b754-84e28c5546da", description="Background image URL")
    title: Optional[str] = Field(default="Render_API_Video", description="Video title")
    width: Optional[int] = Field(default=1280, description="Video width")
    height: Optional[int] = Field(default=720, description="Video height")

class VideoGenerationResponse(BaseModel):
    success: bool
    message: str
    request_id: str
    video_id: Optional[str] = None
    estimated_time: Optional[str] = None

class VideoRetrievalRequest(BaseModel):
    request_id: Optional[str] = None
    video_id: Optional[str] = None

class VideoRetrievalResponse(BaseModel):
    success: bool
    message: str
    request_id: Optional[str] = None
    video_id: Optional[str] = None
    status: Optional[str] = None
    video_url: Optional[str] = None
    caption_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    created_at: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="HeyGen Video Generation API",
    description="API service for generating AI videos using HeyGen - Deployed on Render",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - Render automatically provides these via environment variables
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
TEMPLATE_ID = os.getenv("TEMPLATE_ID", "52df47c0bd8e435c9729121e036d2e7f")  # Can be customized per request
PORT = int(os.getenv("PORT", 8000))

if not HEYGEN_API_KEY:
    logger.warning("HEYGEN_API_KEY environment variable not set")

class HeyGenService:
    """Service class for HeyGen API interactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.heygen.com"
    
    def generate_video(self, request: VideoGenerationRequest) -> Dict[str, Any]:
        """Generate video using HeyGen API"""
        # Use template_id from request or fall back to environment default
        template_id = request.template_id or TEMPLATE_ID
        
        url = f"{self.base_url}/v2/template/{template_id}/generate"
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        
        payload = {
            "caption": request.use_captions,
            "dimension": {
                "width": request.width,
                "height": request.height
            },
            "include_gif": False,
            "title": request.title,
            "variables": {
                "voice_id": {
                    "name": "voice_id",
                    "type": "voice",
                    "properties": {
                        "voice_id": request.voice_id,
                        "locale": None
                    }
                },
                "avatar_id": {
                    "name": "avatar_id",
                    "type": "character",
                    "properties": {
                        "character_id": request.avatar_id,
                        "type": "talking_photo"
                    }
                },
                "background_id": {
                    "name": "background_id",
                    "type": "image",
                    "properties": {
                        "url": request.background_url,
                        "asset_id": None,
                        "fit": "none"
                    }
                },
                "script_content": {
                    "name": "script_content",
                    "type": "text",
                    "properties": {
                        "content": request.script_text
                    }
                }
            },
            "enable_sharing": True
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"HeyGen API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"HeyGen API error: {response.text}"
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=408, detail="Request timeout")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Service unavailable")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get video status from HeyGen API"""
        url = f"{self.base_url}/v1/video_status.get"
        
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        params = {"video_id": video_id}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"HeyGen API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"HeyGen API error: {response.text}"
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=408, detail="Request timeout")
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Service unavailable")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

# Initialize service
heygen_service = None

def get_heygen_service():
    global heygen_service
    if not heygen_service and HEYGEN_API_KEY:
        heygen_service = HeyGenService(HEYGEN_API_KEY)
    return heygen_service

# API Routes
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "HeyGen Video Generation API is running on Render",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": "Render"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check for Render"""
    service = get_heygen_service()
    return {
        "status": "healthy",
        "api_key_configured": bool(HEYGEN_API_KEY),
        "service_initialized": bool(service),
        "template_id": TEMPLATE_ID,
        "port": PORT,
        "platform": "Render",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/generate", response_model=VideoGenerationResponse, tags=["Video Generation"])
async def generate_video(request: VideoGenerationRequest):
    """Generate a new AI video"""
    
    service = get_heygen_service()
    if not service:
        raise HTTPException(
            status_code=500,
            detail="Service not configured. Please set HEYGEN_API_KEY environment variable."
        )
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    try:
        # Call HeyGen API
        result = service.generate_video(request)
        
        if "data" in result and "video_id" in result["data"]:
            video_id = result["data"]["video_id"]
            
            # Store request mapping
            video_requests_db[request_id] = {
                "video_id": video_id,
                "script_text": request.script_text,
                "template_id": request.template_id or TEMPLATE_ID,
                "use_captions": request.use_captions,
                "avatar_id": request.avatar_id,
                "voice_id": request.voice_id,
                "title": request.title,
                "created_at": datetime.now().isoformat(),
                "status": "processing",
                "platform": "render"
            }
            
            logger.info(f"Video generation initiated on Render: request_id={request_id}, video_id={video_id}")
            
            return VideoGenerationResponse(
                success=True,
                message="Video generation initiated successfully",
                request_id=request_id,
                video_id=video_id,
                estimated_time="2-5 minutes"
            )
        else:
            logger.error(f"Unexpected API response: {result}")
            raise HTTPException(
                status_code=500,
                detail="Unexpected response from video generation service"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@app.post("/retrieve", response_model=VideoRetrievalResponse, tags=["Video Retrieval"])
async def retrieve_video(request: VideoRetrievalRequest):
    """Retrieve video status and details"""
    
    service = get_heygen_service()
    if not service:
        raise HTTPException(
            status_code=500,
            detail="Service not configured. Please set HEYGEN_API_KEY environment variable."
        )
    
    video_id = None
    request_id = request.request_id
    
    # Determine video_id from request_id or direct video_id
    if request.request_id:
        if request.request_id in video_requests_db:
            video_id = video_requests_db[request.request_id]["video_id"]
        else:
            raise HTTPException(status_code=404, detail="Request ID not found")
    elif request.video_id:
        video_id = request.video_id
        # Try to find corresponding request_id
        for rid, data in video_requests_db.items():
            if data["video_id"] == video_id:
                request_id = rid
                break
    else:
        raise HTTPException(status_code=400, detail="Either request_id or video_id must be provided")
    
    try:
        # Get video status from HeyGen
        result = service.get_video_status(video_id)
        
        if "data" in result and "status" in result["data"]:
            data = result["data"]
            status = data["status"]
            
            # Update local storage
            if request_id and request_id in video_requests_db:
                video_requests_db[request_id]["status"] = status
                video_requests_db[request_id]["last_checked"] = datetime.now().isoformat()
            
            response_data = {
                "success": True,
                "message": f"Video status: {status}",
                "request_id": request_id,
                "video_id": video_id,
                "status": status
            }
            
            # Add additional data if video is completed
            if status == "completed":
                response_data.update({
                    "video_url": data.get("video_url"),
                    "caption_url": data.get("caption_url"),
                    "thumbnail_url": data.get("thumbnail_url"),
                    "duration": data.get("duration"),
                    "created_at": data.get("created_at")
                })
            elif status == "failed":
                response_data["message"] = f"Video generation failed: {data.get('error', 'Unknown error')}"
            
            logger.info(f"Video status retrieved on Render: video_id={video_id}, status={status}")
            return VideoRetrievalResponse(**response_data)
            
        else:
            logger.error(f"Unexpected API response: {result}")
            raise HTTPException(
                status_code=500,
                detail="Unexpected response from video status service"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video retrieval failed: {str(e)}")

@app.get("/requests", tags=["Management"])
async def list_requests():
    """List all video requests (for debugging/monitoring)"""
    return {
        "platform": "Render",
        "total_requests": len(video_requests_db),
        "requests": video_requests_db
    }

@app.get("/requests/{request_id}", tags=["Management"])
async def get_request_details(request_id: str):
    """Get details of a specific request"""
    if request_id not in video_requests_db:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return video_requests_db[request_id]

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "status_code": exc.status_code, "platform": "Render"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception on Render: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "status_code": 500, "platform": "Render"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
