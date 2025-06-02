# README.md
# HeyGen Video Generation API

A FastAPI service for generating AI videos using HeyGen's API, deployed on Render.

## Features

- 🎬 Generate AI videos with custom scripts
- 🎭 Customizable avatars and voices  
- 📱 REST API endpoints
- 📄 Caption support
- ⚡ Auto-scaling on Render
- 🔄 Request tracking and status monitoring

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd heygen-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your HEYGEN_API_KEY
```

5. Run the application:
```bash
uvicorn main:app --reload
```

6. Visit http://localhost:8000/docs for interactive API documentation

## API Endpoints

### Generate Video
```http
POST /generate
Content-Type: application/json

{
    "script_text": "Hello world!",
    "use_captions": true,
    "title": "My Test Video"
}
```

### Retrieve Video
```http
POST /retrieve
Content-Type: application/json

{
    "request_id": "your-request-id-here"
}
```

### Health Check
```http
GET /health
```

## Deployment on Render

This project is configured for automatic deployment on Render. See the deployment guide below.

## Usage Examples

```python
import requests

BASE_URL = "https://your-app.onrender.com"

# Generate video
response = requests.post(f"{BASE_URL}/generate", json={
    "script_text": "Welcome to our AI video service!",
    "use_captions": True
})

result = response.json()
request_id = result["request_id"]

# Check status
status_response = requests.post(f"{BASE_URL}/retrieve", json={
    "request_id": request_id
})

print(status_response.json())
```

## Environment Variables

- `HEYGEN_API_KEY`: Your HeyGen API key (required)
- `TEMPLATE_ID`: HeyGen template ID (optional, has default)
- `PORT`: Port to run the service (automatically set by Render)

## License

MIT License
