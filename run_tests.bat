@echo off
echo 🚀 Running FansHub Tests...

REM Check if coverage is installed
python -c "import coverage" 2>NUL
if errorlevel 1 (
    echo Installing coverage...
    pip install coverage
)

REM Run tests with coverage
echo.
echo 📊 Running tests with coverage...
python -m coverage run manage.py test -v 2

REM Check if tests passed
if errorlevel 1 (
    echo.
    echo ❌ Tests failed!
    exit /b 1
) else (
    echo.
    echo ✅ All tests passed!
    
    REM Generate coverage report
    echo.
    echo 📈 Generating coverage report...
    python -m coverage report
    
    REM Generate HTML coverage report
    echo.
    echo 📑 Generating HTML coverage report...
    python -m coverage html
    
    echo.
    echo ✨ Coverage report generated in htmlcov/index.html
)

REM Run specific tests
echo.
echo 🚀 Running specific tests...
python manage.py test content.tests.test_posts
python manage.py test subscriptions.tests.test_payment_methods

REM Check if tests passed
if errorlevel 1 (
    echo.
    echo ❌ Tests failed!
    exit /b 1
) else (
    echo.
    echo ✅ All specific tests passed!
) 