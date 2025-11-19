#!/bin/bash

echo ""
echo "========================================"
echo "QuizForge - Quiz Processing Pipeline"
echo "========================================"
echo ""

# Run the orchestrator
python3 engine/orchestrator.py

echo ""
echo "Processing complete."
read -p "Press Enter to exit..."