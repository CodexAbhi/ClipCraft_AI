# ClipCraft AI – AI Video Generator with HeyGen API

**ClipCraft AI** is a full-stack application that lets users generate realistic AI avatar videos using text scripts, captions, and voice input.  
It includes:
- A Streamlit-based frontend for interactive video generation
- A FastAPI backend service for API-based automation and deployment on Render

---

## 🔧 Features

### Frontend (Streamlit)
- Input script via text box
- Toggle captions on/off
- Submit and retrieve generated videos
- Embedded video player with caption support
- Download buttons for video and `.vtt` caption files

### Backend (FastAPI)
- REST API endpoints to:
  - Generate videos via POST
  - Retrieve video status
  - Run health checks
- Deploy-ready on **Render**
- Handles caption support and request tracking

---

## 💻 Local Setup (Backend API)

### 1. Clone and setup virtual environment

```bash
git clone https://github.com/your-username/clipcraft-ai
cd clipcraft-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in your `HEYGEN_API_KEY` in the `.env` file.

### 3. Run the backend

```bash
uvicorn main:app --reload
```

Visit: `http://localhost:8000/docs` for Swagger API docs.

---

## 📜 API Endpoints

### `POST /generate`

**Generate a video**

```json
{
  "script_text": "Welcome to our AI video service!",
  "use_captions": true,
  "title": "My Test Video"
}
```

Returns: `request_id`

---

### `POST /retrieve`

**Get video status and URL**

```json
{
  "request_id": "your-request-id"
}
```

Returns: status, video URL, caption URL (if available)

---

### `GET /health`

**Health check**

---

## Deployment on Render

1. Push your code to a GitHub repo
2. Connect the repo to Render
3. Set environment variables in the Render dashboard:

   * `HEYGEN_API_KEY`
   * `PORT` (automatically handled by Render)

Render will auto-deploy the FastAPI app with public API access.

---

## Streamlit Frontend

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

Visit `http://localhost:8501`

### 3. Features

* Input script
* Enable captions (optional)
* Generate video via HeyGen API
* View status
* Stream video with captions
* Download `.mp4` and `.vtt`

---

## Environment Variables

| Variable         | Description                    |
| ---------------- | ------------------------------ |
| `HEYGEN_API_KEY` | Your HeyGen API Key (required) |
| `TEMPLATE_ID`    | Optional HeyGen template ID    |
| `PORT`           | Set automatically by Render    |

---

## 📦 Requirements

* streamlit
* fastapi
* uvicorn
* requests
* python-dotenv
* audio-recorder-streamlit
* SpeechRecognition
* python-multipart
* PyPDF2, docx2txt (if supporting docs in backend)

Install all with:

```bash
pip install -r requirements.txt
```

---

## Usage Example (API)

```python
import requests

BASE_URL = "https://your-app.onrender.com"

# Generate video
res = requests.post(f"{BASE_URL}/generate", json={
    "script_text": "Hello world!",
    "use_captions": True,
    "title": "My Test Video"
})
request_id = res.json()["request_id"]

# Check status
status = requests.post(f"{BASE_URL}/retrieve", json={"request_id": request_id})
print(status.json())
```

---

## License

MIT License — free to use, build on, and improve.

---

## Acknowledgments

* [HeyGen API](https://www.heygen.com/)
* [Streamlit](https://streamlit.io/)
* [FastAPI](https://fastapi.tiangolo.com/)
