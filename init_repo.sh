#!/bin/bash

# Initialize the git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Working Memory Trainer

Create standalone repository for the Working Memory Trainer application
extracted from my personal configuration system."

echo "Repository initialized successfully!"
echo "You may want to add a remote with:"
echo "  git remote add origin https://github.com/yourusername/working-memory-trainer.git"
echo "Then push with:"
echo "  git push -u origin main"