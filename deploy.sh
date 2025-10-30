#!/bin/bash
# Deployment script for Streamlit app

echo "🚀 Jira Allocations App Deployment Script"
echo "=========================================="

# Function to deploy to Streamlit Cloud
deploy_streamlit_cloud() {
    echo "📝 To deploy to Streamlit Cloud:"
    echo "1. Go to https://share.streamlit.io/"
    echo "2. Connect your GitHub account"
    echo "3. Select repository: thungong/jiraallocate"
    echo "4. Set main file: app_modern.py"
    echo "5. Click Deploy!"
    echo ""
}

# Function to deploy to Heroku
deploy_heroku() {
    echo "📝 To deploy to Heroku:"
    echo "1. Install Heroku CLI"
    echo "2. Run: heroku create your-app-name"
    echo "3. Run: git push heroku main"
    echo ""
    
    # Create Procfile for Heroku
    cat > Procfile << EOF
web: streamlit run app_modern.py --server.port=\$PORT --server.address=0.0.0.0
EOF
    echo "✅ Created Procfile for Heroku"
}

# Function to deploy to Railway
deploy_railway() {
    echo "📝 To deploy to Railway:"
    echo "1. Go to https://railway.app/"
    echo "2. Connect GitHub repository"
    echo "3. Railway will auto-detect Python and deploy"
    echo ""
}

# Function to deploy using Docker
deploy_docker() {
    echo "🐳 Building Docker image..."
    docker build -t jira-allocations .
    echo "✅ Docker image built successfully"
    echo ""
    echo "To run locally:"
    echo "docker run -p 8501:8501 jira-allocations"
    echo ""
    echo "To deploy to cloud providers supporting Docker:"
    echo "- Google Cloud Run"
    echo "- AWS ECS"
    echo "- Azure Container Instances"
}

echo "Available deployment options:"
echo "1. Streamlit Cloud (Recommended - Free)"
echo "2. Heroku"
echo "3. Railway"
echo "4. Docker"
echo ""

read -p "Choose deployment option (1-4): " choice

case $choice in
    1)
        deploy_streamlit_cloud
        ;;
    2)
        deploy_heroku
        ;;
    3)
        deploy_railway
        ;;
    4)
        deploy_docker
        ;;
    *)
        echo "Invalid option. Please run again and choose 1-4."
        ;;
esac