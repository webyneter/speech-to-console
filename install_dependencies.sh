#!/bin/bash
set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing dependencies for speech-to-console on Ubuntu/Debian...${NC}"

# Update package list
echo -e "${YELLOW}Updating package lists...${NC}"
sudo apt-get update

# Install PortAudio and other runtime dependencies
echo -e "${YELLOW}Installing PortAudio and other runtime dependencies...${NC}"
sudo apt-get install -y portaudio19-dev python3-pyaudio

echo -e "\n${GREEN}Runtime dependencies installed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create a .env file with your OpenAI API key:"
echo "   cp example.env .env"
echo "   nano .env  # Edit to add your API key"
echo ""
echo "2. Run the speech-to-console tool:"
echo "   speech-to-console"
echo ""
echo -e "${GREEN}Enjoy using speech-to-console!${NC}"