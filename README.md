# Project

A FastAPI-based web application with retrieval-augmented chat and evaluation capabilities.

## Project Structure

```
project/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── faq.py
│   │   ├── chat.py
│   │   └── eval.py
│   ├── services/
│   │   ├── retrieval.py
│   │   ├── ai.py
│   │   └── scoring.py
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── init_db.py
│   ├── templates/
│   └── static/
├── data/
│   ├── kb.json
│   └── tasks.json
├── scripts/
├── requirements.txt
└── Dockerfile
```

## Installation

```bash
pip install -r requirements.txt
```

## Running Locally

1. Create a `.env` file in the project root with your database and OpenRouter/OpenAI credentials.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

## Docker

Create a `.env` file alongside `docker-compose.yml` with your secret values, then run:

```bash
docker-compose up --build
```

The app will be available at http://localhost:8000.

## Sharing with ngrok

If you want to share the running app with friends, run ngrok after the app starts:

```bash
ngrok http 8000
```

Copy the public URL from ngrok and share it. If you are using OpenRouter, set `OPENROUTER_SITE_URL` to the public ngrok URL in your `.env` file so the backend sends the correct referer header.

## Environment

Use a `.env` file with values like:

```text
DATABASE_URL=sqlite:///./data/faq_mvp.sqlite
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_SITE_URL=https://<your-ngrok-url>
OPENROUTER_APP_NAME=FAQ Chat Application
DEBUG=False
```

If you prefer OpenAI instead of OpenRouter, replace the OpenRouter vars with:

```text
OPENAI_API_KEY=sk-...
OPENAI_TRANSCRIPTION_API_KEY=sk-...
```

## License

MIT
