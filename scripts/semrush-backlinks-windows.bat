@echo off
echo SEMrush backlink pull + optional Selenium cross-link poster
echo.
echo Step 1: Set SEMRUSH_API_KEY in backend .env and restart backend
echo Step 2: Pull backlinks into dashboard
python "%~dp0semrush-pull-backlinks.py"
echo.
echo Step 3 (optional): Post cross-links on YOUR WordPress sites
echo   copy scripts\link-post-config.example.json scripts\link-post-config.json
echo   set WP_SABACABS_USER=... and WP_SABACABS_PASS=...
echo   pip install -r scripts\requirements-selenium.txt
echo   python scripts\post-portfolio-links-selenium.py
pause
