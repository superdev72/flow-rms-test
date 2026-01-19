#!/bin/bash
# Setup script for the project

echo "Setting up Invoice Reconciliation API..."

# Create virtual environment
echo "Creating virtual environment..."
python3.13 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Or use: ./run.sh"
