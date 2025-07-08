#!/bin/bash

# AWS Cloud Utilities v2 - Test Runner Script
# This script runs the comprehensive test suite with various configurations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGION="us-east-1"
PROFILE=""
VERBOSE=false
DRY_RUN=false
OUTPUT_DIR="./test_results"
CONFIG_FILE="./test_config.yaml"
PARALLEL=false

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
AWS Cloud Utilities v2 - Test Runner

Usage: $0 [OPTIONS]

Options:
    -r, --region REGION         AWS region for testing (default: us-east-1)
    -p, --profile PROFILE       AWS profile to use
    -v, --verbose               Enable verbose output
    -d, --dry-run              Show what would be tested without executing
    -o, --output-dir DIR        Output directory for test results (default: ./test_results)
    -c, --config FILE           Test configuration file (default: ./test_config.yaml)
    --parallel                  Run tests in parallel (experimental)
    --quick                     Run only quick tests (skip slow operations)
    --ci                        CI mode (non-interactive, structured output)
    -h, --help                  Show this help message

Examples:
    # Run all tests with default settings
    $0

    # Run tests with specific profile and region
    $0 --profile dev --region us-west-2

    # Run quick tests only
    $0 --quick

    # Dry run to see what would be tested
    $0 --dry-run

    # CI mode with structured output
    $0 --ci --output-dir ./ci_results

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --ci)
            CI_MODE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Print header
if [[ "$CI_MODE" != "true" ]]; then
    print_status $BLUE "🧪 AWS Cloud Utilities v2 - Test Runner"
    print_status $BLUE "=================================================="
    echo
fi

# Check if we're in the right directory
if [[ ! -f "test_comprehensive.py" ]]; then
    print_status $RED "❌ Error: test_comprehensive.py not found"
    print_status $RED "Please run this script from the v2 directory"
    exit 1
fi

# Check Python environment
if ! python3 -c "import aws_cloud_utilities" 2>/dev/null; then
    print_status $YELLOW "⚠️  Installing package in development mode..."
    pip install -e .
fi

# Build test command
TEST_CMD="python3 test_comprehensive.py"

# Add region
TEST_CMD="$TEST_CMD --region $REGION"

# Add profile if specified
if [[ -n "$PROFILE" ]]; then
    TEST_CMD="$TEST_CMD --profile $PROFILE"
fi

# Add verbose flag
if [[ "$VERBOSE" == "true" ]]; then
    TEST_CMD="$TEST_CMD --verbose"
fi

# Add dry-run flag
if [[ "$DRY_RUN" == "true" ]]; then
    TEST_CMD="$TEST_CMD --dry-run"
fi

# Add output file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="$OUTPUT_DIR/test_results_$TIMESTAMP.json"
TEST_CMD="$TEST_CMD --output-file $OUTPUT_FILE"

# Print test configuration
if [[ "$CI_MODE" != "true" ]]; then
    print_status $BLUE "Test Configuration:"
    echo "  Region: $REGION"
    echo "  Profile: ${PROFILE:-default}"
    echo "  Verbose: $VERBOSE"
    echo "  Dry Run: $DRY_RUN"
    echo "  Output Dir: $OUTPUT_DIR"
    echo "  Output File: $OUTPUT_FILE"
    echo
fi

# Check AWS credentials
if [[ "$DRY_RUN" != "true" ]]; then
    if [[ -n "$PROFILE" ]]; then
        if ! aws sts get-caller-identity --profile "$PROFILE" >/dev/null 2>&1; then
            print_status $YELLOW "⚠️  Warning: AWS credentials not available for profile '$PROFILE'"
            print_status $YELLOW "Some tests may be skipped"
        fi
    else
        if ! aws sts get-caller-identity >/dev/null 2>&1; then
            print_status $YELLOW "⚠️  Warning: AWS credentials not available"
            print_status $YELLOW "Some tests may be skipped"
        fi
    fi
fi

# Run the tests
print_status $BLUE "🚀 Starting test execution..."
echo

# Execute the test command
if eval "$TEST_CMD"; then
    TEST_EXIT_CODE=0
    if [[ "$CI_MODE" == "true" ]]; then
        echo "TEST_STATUS=PASSED"
    else
        print_status $GREEN "✅ Tests completed successfully!"
    fi
else
    TEST_EXIT_CODE=$?
    if [[ "$CI_MODE" == "true" ]]; then
        echo "TEST_STATUS=FAILED"
    else
        print_status $RED "❌ Some tests failed"
    fi
fi

# Process results if output file exists
if [[ -f "$OUTPUT_FILE" ]]; then
    # Extract key metrics
    TOTAL_TESTS=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print(data.get('total_tests', 0))")
    PASSED_TESTS=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print(data.get('passed_tests', 0))")
    FAILED_TESTS=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print(data.get('failed_tests', 0))")
    SUCCESS_RATE=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print(f\"{data.get('success_rate', 0):.1f}\")")
    DURATION=$(python3 -c "import json; data=json.load(open('$OUTPUT_FILE')); print(f\"{data.get('duration', 0):.2f}\")")
    
    if [[ "$CI_MODE" == "true" ]]; then
        # CI-friendly output
        echo "TOTAL_TESTS=$TOTAL_TESTS"
        echo "PASSED_TESTS=$PASSED_TESTS"
        echo "FAILED_TESTS=$FAILED_TESTS"
        echo "SUCCESS_RATE=$SUCCESS_RATE"
        echo "DURATION=$DURATION"
        echo "OUTPUT_FILE=$OUTPUT_FILE"
    else
        # Human-friendly summary
        echo
        print_status $BLUE "📊 Final Summary:"
        echo "  Total Tests: $TOTAL_TESTS"
        echo "  Passed: $PASSED_TESTS"
        echo "  Failed: $FAILED_TESTS"
        echo "  Success Rate: $SUCCESS_RATE%"
        echo "  Duration: ${DURATION}s"
        echo "  Results: $OUTPUT_FILE"
    fi
fi

# Generate HTML report if jq is available
if command -v jq >/dev/null 2>&1 && [[ -f "$OUTPUT_FILE" ]]; then
    HTML_REPORT="$OUTPUT_DIR/test_report_$TIMESTAMP.html"
    
    cat > "$HTML_REPORT" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>AWS Cloud Utilities v2 - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .details { margin-top: 20px; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AWS Cloud Utilities v2 - Test Report</h1>
        <p>Generated: $(date)</p>
        <p>Region: $REGION | Profile: ${PROFILE:-default}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div style="font-size: 24px;">$TOTAL_TESTS</div>
        </div>
        <div class="metric">
            <h3 class="passed">Passed</h3>
            <div style="font-size: 24px;">$PASSED_TESTS</div>
        </div>
        <div class="metric">
            <h3 class="failed">Failed</h3>
            <div style="font-size: 24px;">$FAILED_TESTS</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div style="font-size: 24px;">$SUCCESS_RATE%</div>
        </div>
    </div>
    
    <div class="details">
        <h2>Detailed Results</h2>
        <pre>$(cat "$OUTPUT_FILE" | jq '.' 2>/dev/null || cat "$OUTPUT_FILE")</pre>
    </div>
</body>
</html>
EOF
    
    if [[ "$CI_MODE" != "true" ]]; then
        print_status $GREEN "📄 HTML report generated: $HTML_REPORT"
    fi
fi

# Cleanup old test results (keep last 10)
find "$OUTPUT_DIR" -name "test_results_*.json" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
find "$OUTPUT_DIR" -name "test_report_*.html" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true

# Exit with the same code as the test
exit $TEST_EXIT_CODE
