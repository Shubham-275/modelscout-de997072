#!/bin/bash

# ModelScout Quick Deploy Script
# This script helps you deploy to various platforms

echo "🚀 ModelScout Deployment Helper"
echo "================================"
echo ""
echo "Choose your deployment platform:"
echo "1) Vercel (Frontend) + Render (Backend) - Recommended"
echo "2) Railway (Full Stack)"
echo "3) Docker (Local/VPS)"
echo "4) Build for production (manual deploy)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
  1)
    echo ""
    echo "📦 Vercel + Render Deployment"
    echo "=============================="
    echo ""
    echo "Frontend (Vercel):"
    echo "1. Go to https://vercel.com"
    echo "2. Import your GitHub repository"
    echo "3. Set VITE_API_URL to your Render backend URL"
    echo ""
    echo "Backend (Render):"
    echo "1. Go to https://render.com"
    echo "2. Create new Web Service"
    echo "3. Connect GitHub repo, select 'backend' folder"
    echo "4. Add environment variables (MINO_API_KEY, etc.)"
    echo ""
    read -p "Press Enter to open deployment guide..."
    cat DEPLOYMENT.md
    ;;
  
  2)
    echo ""
    echo "🚂 Railway Deployment"
    echo "===================="
    echo ""
    echo "1. Go to https://railway.app"
    echo "2. Create new project from GitHub"
    echo "3. Add services for frontend and backend"
    echo "4. Configure environment variables"
    echo ""
    read -p "Press Enter to open deployment guide..."
    cat DEPLOYMENT.md
    ;;
  
  3)
    echo ""
    echo "🐳 Docker Deployment"
    echo "==================="
    echo ""
    echo "Building containers..."
    docker-compose build
    echo ""
    echo "Starting services..."
    docker-compose up -d
    echo ""
    echo "✅ Services started!"
    echo "Frontend: http://localhost"
    echo "Backend: http://localhost:5000"
    echo ""
    echo "To stop: docker-compose down"
    ;;
  
  4)
    echo ""
    echo "🔨 Building for Production"
    echo "=========================="
    echo ""
    echo "Building frontend..."
    npm run build
    echo ""
    echo "✅ Build complete!"
    echo "Files are in: ./dist"
    echo ""
    echo "Deploy 'dist' folder to:"
    echo "- Netlify"
    echo "- Vercel"
    echo "- GitHub Pages"
    echo "- Any static hosting"
    ;;
  
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac
