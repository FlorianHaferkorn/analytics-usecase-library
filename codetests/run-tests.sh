#!/bin/bash
# ATLAS Backend Test Runner
# Usage: ./scripts/run-tests.sh [test_path] [options]
#
# Examples:
#   ./scripts/run-tests.sh                    # Run all tests
#   ./scripts/run-tests.sh tests/models/      # Run model tests only
#   ./scripts/run-tests.sh -v                 # Verbose mode
#   ./scripts/run-tests.sh --cov              # With coverage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ATLAS Backend Test Runner${NC}"
echo -e "${GREEN}========================================${NC}"

cd "$BACKEND_DIR"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set database URL if not set
export DATABASE_URL="${DATABASE_URL:-postgresql://aaldertoosthuizen@localhost:5432/aims_db}"

# Parse arguments
TEST_PATH="${1:-tests/}"
EXTRA_ARGS=""

if [[ "$1" == "-"* ]]; then
    TEST_PATH="tests/"
    EXTRA_ARGS="$@"
else
    shift 2>/dev/null || true
    EXTRA_ARGS="$@"
fi

echo -e "\n${YELLOW}Running tests: $TEST_PATH${NC}"
echo -e "${YELLOW}Database: $DATABASE_URL${NC}\n"

# Run tests
python -m pytest "$TEST_PATH" $EXTRA_ARGS

echo -e "\n${GREEN}Tests completed!${NC}"
