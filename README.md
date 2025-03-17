# Presale Assistance API

A backend API for a presale assistance system powered by Google's Gemini LLM model and VertexAI. This system processes company PowerPoint presentations stored in Google Drive, extracts their content, and uses it to provide intelligent responses to prompts related to company information, capabilities, and previous bids.

## Features

- Integration with Google Drive to access PowerPoint presentations
- Text extraction from PowerPoint files
- Vector embeddings for semantic search of document content
- Integration with Google's Gemini LLM model for intelligent responses
- RESTful API for sending prompts and receiving responses

## Prerequisites

- Python 3.9+
- Google Cloud Platform account with VertexAI enabled
- Google Drive folder containing company PowerPoint presentations
- Google Cloud service account with access to Drive and VertexAI

## Setup

1. Clone the repository

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example` and fill in your configuration:

   ```
   cp .env.example .env
   ```

4. Set up Google Cloud credentials:

   - Create a service account in Google Cloud Console
   - Grant it access to Drive API and VertexAI
   - Download the service account key JSON file
   - Set the path to this file in the `.env` file

5. Configure the Google Drive folder ID containing your PowerPoint presentations in the `.env` file

## Running the API

Start the API server:

```
python main.py
```

The API will be available at http://localhost:8000

## API Endpoints

- `GET /` - Health check endpoint
- `POST /api/prompt` - Send a prompt to the presale assistant
- `GET /api/status` - Get the status of the presale assistant

## Authentication

The API uses JWT token-based authentication. You'll need to implement a token generation endpoint or use an external authentication provider.

## Example Usage

```python
import requests

# Replace with your actual token
token = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "prompt": "What are our company's main capabilities in cloud infrastructure?",
    "context": {
        "client": "Example Corp",
        "opportunity": "Cloud Migration Project"
    }
}

response = requests.post(
    "http://localhost:8000/api/prompt",
    json=data,
    headers=headers
)

print(response.json())
```

## License

This project is proprietary and confidential.
# presale-assistance-backend
