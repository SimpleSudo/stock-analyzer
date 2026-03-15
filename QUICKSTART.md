# Stock Analyzer Project

## Backend
- Running on: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## Frontend
- Running on: http://localhost:5173

## To stop the background processes:
1. Find the process IDs: 
   - Backend: `ps aux | grep 'python.*main'`
   - Frontend: `ps aux | grep 'npm run dev'`
2. Kill the processes:
   - Backend: `kill <PID>`
   - Frontend: `kill <PID>`

## Development
- Backend: `cd backend && source venv/bin/activate && python -m src.main`
- Frontend: `cd frontend && npm run dev`
