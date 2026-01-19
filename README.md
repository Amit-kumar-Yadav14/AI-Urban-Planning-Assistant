# Urban Planning Assistant

An AI-powered urban planning assistant that routes citizen reports to the correct city department, collects required information, and sends data via webhook.

## Features

- Natural language understanding for citizen reports
- Automatic routing to three departments:
  - Traffic & Transport
  - Waste Management
  - Green Energy & Spaces
- Intelligent data collection with clarification questions
- Supabase integration for state management
- Webhook notifications when reports are complete

## Tech Stack

- **Frontend**: React (Vite)
- **Backend**: FastAPI
- **AI Flow**: LangGraph
- **Database**: Supabase (PostgreSQL)

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
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

4. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Fill in your environment variables:
```
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
WEBHOOK_URL=your_webhook_url_here
```

6. Set up Supabase database:
   - Create a table named `conversations` with the following schema:
   ```sql
   CREATE TABLE conversations (
     id BIGSERIAL PRIMARY KEY,
     session_id TEXT UNIQUE NOT NULL,
     department TEXT,
     location TEXT,
     issue_description TEXT,
     severity_level INTEGER,
     status TEXT,
     last_message TEXT,
     ai_response TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

7. Run the backend:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## API Endpoints

### POST /chat

Send a message to the assistant.

**Request:**
```json
{
  "message": "There's a pothole on Main Street",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "Thank you for reporting this issue...",
  "session_id": "uuid",
  "department": "traffic",
  "status": "in_progress"
}
```

### GET /health

Health check endpoint.

## Webhook Payload

When a report is complete, the system sends a POST request to the configured webhook URL:

```json
{
  "location": "Main Street, Downtown",
  "issue_description": "Large pothole causing traffic issues",
  "severity_level": 7,
  "department": "traffic"
}
```

## Project Structure

```
csr/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── langgraph_workflow.py   # LangGraph conversation flow
│   ├── supabase_client.py      # Supabase integration
│   ├── webhook_client.py       # Webhook sender
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── App.css             # Styles
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Global styles
│   ├── index.html              # HTML template
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite configuration
└── README.md                    # This file
```

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:5173` in your browser
3. Type a message describing your issue (e.g., "There's trash piling up at the park")
4. The assistant will route your message and ask for any missing information
5. Once all required fields are collected, the report is submitted via webhook

## Required Information

Each report requires:
- **Location**: Address, coordinates, or landmark
- **Issue Description**: Detailed description of the problem
- **Severity Level**: Number from 1-10 (1 = minor, 10 = critical)

## Notes

- The system maintains conversation state using session IDs
- Each department node asks for one missing field at a time
- Webhooks are only triggered when all required fields are present
- The assistant uses GPT-3.5-turbo for intent classification and information extraction
