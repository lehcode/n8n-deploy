#!/bin/bash
# Script to test GitHub Pages documentation locally

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== GitHub Pages Local Test Environment ===${NC}\n"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Build and start the container
echo -e "${GREEN}Building Docker container...${NC}"
docker compose -f docker-compose.ghpages.yml build

echo -e "\n${GREEN}Starting Jekyll server...${NC}"
docker compose -f docker-compose.ghpages.yml up -d

# Wait for Jekyll to start
echo -e "\n${BLUE}Waiting for Jekyll to start...${NC}"
sleep 5

# Check if container is running
if docker ps | grep -q n8n-deploy-ghpages; then
    echo -e "\n${GREEN}✓ Jekyll server is running!${NC}"
    echo -e "\n${BLUE}Access your documentation at:${NC}"
    echo -e "  ${GREEN}http://localhost:4000/n8n-deploy/${NC}"
    echo -e "\n${BLUE}LiveReload is enabled - changes will auto-refresh${NC}"
    echo -e "\n${YELLOW}View logs:${NC} docker compose -f docker-compose.ghpages.yml logs -f"
    echo -e "${YELLOW}Stop server:${NC} docker compose -f docker-compose.ghpages.yml down"
else
    echo -e "\n${YELLOW}Error: Container failed to start. Check logs with:${NC}"
    echo -e "  docker compose -f docker-compose.ghpages.yml logs"
    exit 1
fi
