# Frontend Integration Setup

This document describes the setup for the NuxtUI-based frontend with FastAPI bridge integration.

## Architecture Overview

```
Frontend (Nuxt.js + NuxtUI) <---> FastAPI Bridge <---> Streamlit Backend
Port 3000                         Port 8000           Existing Streamlit
```

## Quick Start

### 1. Start the FastAPI Bridge Server

```bash
# From project root
./start_api.sh
```

This will start the FastAPI server on `http://localhost:8000`

### 2. Start the Frontend

```bash
# From project root
./frontend/start_frontend.sh
```

This will:
- Install npm packages if needed
- Start the Nuxt.js development server on `http://localhost:3000`

### 3. Access the Application

Open your browser to `http://localhost:3000` to access the new NuxtUI frontend.

## Features

### Frontend (NuxtUI)
- Modern, responsive design using NuxtUI components
- Real-time weather comment generation
- **Single location and batch generation modes**
- Location selection from loaded data
- LLM provider selection (OpenAI, Gemini, Claude)
- **Configurable forecast window (1-72 hours)**
- **Weather range analysis (±24 hours around target time)**
- Generation history display
- **Detailed weather metadata display with forecast range info**
- Error handling with user-friendly messages

### FastAPI Bridge
- RESTful API endpoints for frontend integration
- Connects to existing Streamlit backend workflow
- Maintains all existing functionality
- CORS enabled for frontend access

## API Endpoints

- `GET /health` - Health check
- `GET /api/locations` - Get available locations
- `GET /api/providers` - Get available LLM providers
- `GET /api/history` - Get generation history
- `POST /api/generate` - Generate weather comment

## Development

### Frontend Development
The frontend uses:
- **Nuxt 3** as the framework
- **NuxtUI** for components and styling
- **TypeScript** for type safety
- **Tailwind CSS** for additional styling

### Backend Integration
The FastAPI bridge server:
- Uses the existing `run_comment_generation` workflow
- Maintains compatibility with Streamlit backend
- Provides JSON API responses for frontend consumption

## Environment Variables

Make sure these are set in your `.env` file:
- `OPENAI_API_KEY` (for OpenAI provider)
- `GEMINI_API_KEY` (for Gemini provider)
- `ANTHROPIC_API_KEY` (for Claude provider)
- `WXTECH_API_KEY` (for weather data)
- AWS credentials for S3 access

## Fallback Behavior

The frontend includes fallback behavior when the API is unavailable:
- Mock location data
- Mock provider data
- Graceful error handling

## Next Steps

1. Customize the UI design and components as needed
2. Add additional features like bulk generation
3. Implement real-time updates
4. Add more detailed error handling
5. Consider adding authentication if needed