#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Running FansHub Tests..."

# Check if coverage is installed
if ! command -v coverage &> /dev/null; then
    echo "Installing coverage..."
    pip install coverage
fi

# Run tests with coverage
echo "\n📊 Running tests with coverage..."
coverage run manage.py test -v 2

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    
    # Generate coverage report
    echo "\n📈 Generating coverage report..."
    coverage report
    
    # Generate HTML coverage report
    echo "\n📑 Generating HTML coverage report..."
    coverage html
    
    echo -e "\n${GREEN}✨ Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "\n${RED}❌ Tests failed!${NC}"
    exit 1
fi 