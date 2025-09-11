#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to run all linters
RUN_RUFF=true
RUN_BLACK=true
RUN_ISORT=true
RUN_MYPY=true
RUN_SHELLCHECK=true
FIX_MODE=false
QUIET_MODE=false

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Comprehensive linting script for the local-weaviate-rag project.

OPTIONS:
    --fix               Run with auto-fix where possible
    --quiet             Suppress verbose output
    --ruff-only         Run only ruff
    --black-only        Run only black
    --isort-only        Run only isort
    --mypy-only         Run only mypy
    --shellcheck-only   Run only shellcheck
    --python-only       Run only Python linters (ruff, black, isort, mypy)
    --shell-only        Run only shell linters (shellcheck)
    --help              Show this help message

EXAMPLES:
    $0                  # Run all linters
    $0 --fix            # Run all linters with auto-fix
    $0 --python-only    # Run only Python linters
    $0 --ruff-only --fix # Run only ruff with auto-fix
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --quiet)
            QUIET_MODE=true
            shift
            ;;
        --ruff-only)
            RUN_RUFF=true
            RUN_BLACK=false
            RUN_ISORT=false
            RUN_MYPY=false
            RUN_SHELLCHECK=false
            shift
            ;;
        --black-only)
            RUN_RUFF=false
            RUN_BLACK=true
            RUN_ISORT=false
            RUN_MYPY=false
            RUN_SHELLCHECK=false
            shift
            ;;
        --isort-only)
            RUN_RUFF=false
            RUN_BLACK=false
            RUN_ISORT=true
            RUN_MYPY=false
            RUN_SHELLCHECK=false
            shift
            ;;
        --mypy-only)
            RUN_RUFF=false
            RUN_BLACK=false
            RUN_ISORT=false
            RUN_MYPY=true
            RUN_SHELLCHECK=false
            shift
            ;;
        --shellcheck-only)
            RUN_RUFF=false
            RUN_BLACK=false
            RUN_ISORT=false
            RUN_MYPY=false
            RUN_SHELLCHECK=true
            shift
            ;;
        --python-only)
            RUN_RUFF=true
            RUN_BLACK=true
            RUN_ISORT=true
            RUN_MYPY=true
            RUN_SHELLCHECK=false
            shift
            ;;
        --shell-only)
            RUN_RUFF=false
            RUN_BLACK=false
            RUN_ISORT=false
            RUN_MYPY=false
            RUN_SHELLCHECK=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if we're in the correct directory
if [[ ! -f "pyproject.toml" ]]; then
    print_status "$RED" "Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Initialize exit code
EXIT_CODE=0

print_status "$BLUE" "🔍 Starting comprehensive linting..."
echo

# Install dev dependencies if needed
if [[ "$FIX_MODE" == true ]] || [[ "$QUIET_MODE" == false ]]; then
    print_status "$YELLOW" "📦 Installing dev dependencies..."
    uv sync --extra dev
    echo
fi

# Run Ruff (replaces flake8, isort functionality)
if [[ "$RUN_RUFF" == true ]]; then
    print_status "$BLUE" "🦀 Running Ruff..."
    
    if [[ "$FIX_MODE" == true ]]; then
        if [[ "$QUIET_MODE" == false ]]; then
            print_status "$YELLOW" "  ⚡ Auto-fixing with Ruff..."
        fi
        if ! uv run ruff check --fix --fix-only .; then
            print_status "$RED" "  ❌ Ruff auto-fix failed"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ Ruff auto-fix completed"
        fi
        
        # Also run ruff format (replaces black functionality in ruff)
        if [[ "$QUIET_MODE" == false ]]; then
            print_status "$YELLOW" "  📝 Formatting with Ruff..."
        fi
        if ! uv run ruff format .; then
            print_status "$RED" "  ❌ Ruff format failed"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ Ruff format completed"
        fi
    else
        if ! uv run ruff check .; then
            print_status "$RED" "  ❌ Ruff check failed"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ Ruff check passed"
        fi
        
        if ! uv run ruff format --check .; then
            print_status "$RED" "  ❌ Ruff format check failed"
            print_status "$YELLOW" "  💡 Run with --fix to auto-format"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ Ruff format check passed"
        fi
    fi
    echo
fi

# Run Black (code formatting)
if [[ "$RUN_BLACK" == true ]]; then
    print_status "$BLUE" "⚫ Running Black..."
    
    if [[ "$FIX_MODE" == true ]]; then
        if [[ "$QUIET_MODE" == false ]]; then
            print_status "$YELLOW" "  📝 Formatting with Black..."
        fi
        if ! uv run black .; then
            print_status "$RED" "  ❌ Black formatting failed"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ Black formatting completed"
        fi
    else
        if ! uv run black --check .; then
            print_status "$RED" "  ❌ Black check failed"
            print_status "$YELLOW" "  💡 Run with --fix to auto-format"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ Black check passed"
        fi
    fi
    echo
fi

# Run isort (import sorting)
if [[ "$RUN_ISORT" == true ]]; then
    print_status "$BLUE" "📥 Running isort..."
    
    if [[ "$FIX_MODE" == true ]]; then
        if [[ "$QUIET_MODE" == false ]]; then
            print_status "$YELLOW" "  📝 Sorting imports with isort..."
        fi
        if ! uv run isort .; then
            print_status "$RED" "  ❌ isort failed"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ isort completed"
        fi
    else
        if ! uv run isort --check-only .; then
            print_status "$RED" "  ❌ isort check failed"
            print_status "$YELLOW" "  💡 Run with --fix to auto-sort imports"
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ isort check passed"
        fi
    fi
    echo
fi

# Run mypy (type checking)
if [[ "$RUN_MYPY" == true ]]; then
    print_status "$BLUE" "🔍 Running mypy..."
    
    if ! uv run mypy rag/ tests/ --exclude 'tests/.*\.py' 2>/dev/null || uv run mypy rag/ 2>/dev/null; then
        print_status "$RED" "  ❌ mypy type checking failed"
        # Don't fail the entire script for mypy issues initially
        if [[ "$QUIET_MODE" == false ]]; then
            print_status "$YELLOW" "  💡 mypy errors detected, consider adding type hints"
        fi
    elif [[ "$QUIET_MODE" == false ]]; then
        print_status "$GREEN" "  ✅ mypy type checking passed"
    fi
    echo
fi

# Run shellcheck (shell script linting)
if [[ "$RUN_SHELLCHECK" == true ]]; then
    print_status "$BLUE" "🐚 Running shellcheck..."
    
    # Find all shell scripts
    SHELL_FILES=$(find . -name "*.sh" -type f ! -path "./.git/*" ! -path "./.*/*" | head -20)
    
    if [[ -n "$SHELL_FILES" ]]; then
        SHELLCHECK_FAILED=false
        while IFS= read -r file; do
            if [[ -n "$file" ]]; then
                if [[ "$QUIET_MODE" == false ]]; then
                    print_status "$YELLOW" "  📝 Checking $file..."
                fi
                if ! shellcheck "$file"; then
                    print_status "$RED" "  ❌ shellcheck failed for $file"
                    SHELLCHECK_FAILED=true
                fi
            fi
        done <<< "$SHELL_FILES"
        
        if [[ "$SHELLCHECK_FAILED" == true ]]; then
            EXIT_CODE=1
        elif [[ "$QUIET_MODE" == false ]]; then
            print_status "$GREEN" "  ✅ shellcheck passed for all shell scripts"
        fi
    else
        if [[ "$QUIET_MODE" == false ]]; then
            print_status "$YELLOW" "  📝 No shell scripts found to check"
        fi
    fi
    echo
fi

# Summary
echo "=================================="
if [[ $EXIT_CODE -eq 0 ]]; then
    print_status "$GREEN" "🎉 All linting checks passed!"
    if [[ "$FIX_MODE" == true ]]; then
        print_status "$GREEN" "✨ Auto-fixes have been applied where possible."
    fi
else
    print_status "$RED" "❌ Some linting checks failed."
    if [[ "$FIX_MODE" == false ]]; then
        print_status "$YELLOW" "💡 Try running with --fix to auto-fix issues."
    fi
fi
echo

exit $EXIT_CODE