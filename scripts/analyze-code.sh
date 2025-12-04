#!/bin/bash
# Code analysis script for n8n-deploy
# Runs various static analysis tools to identify code quality issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/api"
TESTS_DIR="$PROJECT_ROOT/tests"
UNIT_TESTS_DIR="$TESTS_DIR/unit"
INTEGRATION_TESTS_DIR="$TESTS_DIR/integration"

echo "========================================"
echo "n8n-deploy Code Analysis"
echo "========================================"
echo ""

# Check if tools are installed
for tool in radon vulture; do
    if ! command -v $tool &> /dev/null; then
        echo "Error: $tool is not installed. Run: pip install $tool"
        exit 1
    fi
done

# Run from temp dir to avoid pyproject.toml parsing issues with radon
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "=== Cyclomatic Complexity (target: A-B) ==="
echo "Grade scale: A (1-5), B (6-10), C (11-20), D (21-30), E (31-40), F (41+)"
echo ""
cd "$TEMP_DIR" && radon cc "$API_DIR" -a -s
echo ""

echo "=== Maintainability Index ==="
echo "Scale: A (20+), B (10-19), C (0-9)"
echo ""
cd "$TEMP_DIR" && radon mi "$API_DIR" -s
echo ""

cd "$PROJECT_ROOT"
echo "=== Unused Code Detection ==="
echo "(min-confidence 80%)"
echo ""
vulture "$API_DIR" --min-confidence 80 || true
echo ""

echo "=== API File Line Counts (>300 lines) ==="
echo ""
find "$API_DIR" -name "*.py" -exec wc -l {} \; | sort -rn | head -20
echo ""

echo "========================================"
echo "Test Analysis"
echo "========================================"
echo ""

echo "=== Test File Line Counts (>500 lines) ==="
echo ""
find "$TESTS_DIR" -name "*.py" -exec wc -l {} \; | sort -rn | head -15
echo ""

echo "=== Test Complexity (target: A-B) ==="
echo ""
cd "$TEMP_DIR" && radon cc "$TESTS_DIR" -a -s --total-average 2>/dev/null || echo "No complexity issues found"
echo ""

echo "=== Unit Tests Summary ==="
echo ""
if [ -d "$UNIT_TESTS_DIR" ]; then
    unit_files=$(find "$UNIT_TESTS_DIR" -name "test_*.py" | wc -l)
    unit_classes=$(grep -rh "^class Test" "$UNIT_TESTS_DIR" 2>/dev/null | wc -l)
    unit_methods=$(grep -rh "def test_" "$UNIT_TESTS_DIR" 2>/dev/null | wc -l)
    echo "  Test files:   $unit_files"
    echo "  Test classes: $unit_classes"
    echo "  Test methods: $unit_methods"
else
    echo "  Unit tests directory not found"
fi
echo ""

echo "=== Integration Tests Summary ==="
echo ""
if [ -d "$INTEGRATION_TESTS_DIR" ]; then
    int_files=$(find "$INTEGRATION_TESTS_DIR" -name "test_*.py" | wc -l)
    int_classes=$(grep -rh "^class Test" "$INTEGRATION_TESTS_DIR" 2>/dev/null | wc -l)
    int_methods=$(grep -rh "def test_" "$INTEGRATION_TESTS_DIR" 2>/dev/null | wc -l)
    echo "  Test files:   $int_files"
    echo "  Test classes: $int_classes"
    echo "  Test methods: $int_methods"

    echo ""
    echo "  By category:"
    for subdir in "$INTEGRATION_TESTS_DIR"/*/; do
        if [ -d "$subdir" ]; then
            category=$(basename "$subdir")
            cat_methods=$(grep -rh "def test_" "$subdir" 2>/dev/null | wc -l)
            if [ "$cat_methods" -gt 0 ]; then
                printf "    %-15s %d tests\n" "$category:" "$cat_methods"
            fi
        fi
    done
else
    echo "  Integration tests directory not found"
fi
echo ""

echo "=== Test Helpers Analysis ==="
echo ""
if [ -f "$TESTS_DIR/helpers.py" ]; then
    helper_funcs=$(grep -c "^def " "$TESTS_DIR/helpers.py" 2>/dev/null || echo "0")
    helper_classes=$(grep -c "^class " "$TESTS_DIR/helpers.py" 2>/dev/null || echo "0")
    helper_lines=$(wc -l < "$TESTS_DIR/helpers.py")
    echo "  helpers.py: $helper_lines lines, $helper_funcs functions, $helper_classes classes"
else
    echo "  helpers.py not found"
fi

if [ -f "$TESTS_DIR/conftest.py" ]; then
    conftest_fixtures=$(grep -c "@pytest.fixture" "$TESTS_DIR/conftest.py" 2>/dev/null || echo "0")
    conftest_lines=$(wc -l < "$TESTS_DIR/conftest.py")
    echo "  conftest.py: $conftest_lines lines, $conftest_fixtures fixtures"
fi
echo ""

echo "=== Duplicate Test Patterns ==="
echo "(Checking for repeated assertion functions)"
echo ""
dup_assert_json=$(grep -rh "def assert_json_output_valid" "$TESTS_DIR" 2>/dev/null | wc -l)
dup_assert_workflow=$(grep -rh "def assert_workflow_" "$TESTS_DIR" 2>/dev/null | wc -l)
echo "  assert_json_output_valid: $dup_assert_json occurrences"
echo "  assert_workflow_*:        $dup_assert_workflow occurrences"
echo ""

echo "========================================"
echo "Analysis Complete"
echo "========================================"
