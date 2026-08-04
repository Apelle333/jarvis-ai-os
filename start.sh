#!/bin/bash

echo "Starting JARVIS AI Operating System..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo "Shutting down JARVIS..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting backend service..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 5

# Start frontend
echo "Starting frontend service..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Both services have been started."
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services."

# Wait for either process to finish
wait -n