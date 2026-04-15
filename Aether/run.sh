#!/bin/bash

# Air Quality Monitoring System Startup Script

echo "🌍 Starting Air Quality Monitoring System..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy historical data to the expected location
if [ -f "historical_readings.csv" ]; then
    echo "📊 Historical data found, system ready."
else
    echo "⚠️  Warning: historical_readings.csv not found in current directory."
    echo "   The system will start but historical endpoints may not work."
fi

# Start the server
echo "🚀 Starting server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🗺️  Real-time Map: http://localhost:8000/map"
echo ""
echo "Press Ctrl+C to stop the server"

python -m uvicorn src.aether.main:app --host 0.0.0.0 --port 8000 --reload