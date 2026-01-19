# Backend - Urban Planning Assistant

FastAPI backend with LangGraph workflow for processing citizen reports.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
OPENAI_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
WEBHOOK_URL=your_webhook_url_here
```

3. Run the server:
```bash
python main.py
```

## Architecture

- `main.py`: FastAPI server and endpoints
- `langgraph_workflow.py`: LangGraph conversation workflow
- `supabase_client.py`: Supabase client initialization

The workflow maintains conversation state per session and routes messages through department-specific data collection nodes.

