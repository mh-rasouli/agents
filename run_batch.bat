@echo off
REM Batch processing script for Google Sheets brands
REM اسکریپت پردازش دسته‌ای برندها از Google Sheets

echo ============================================================
echo Brand Intelligence Agent - Batch Processing
echo پردازش دسته‌ای برندها
echo ============================================================
echo.

REM Set your credentials
SET CREDENTIALS=C:\Users\TrendAgency\Downloads\claude-agents-487515-27f459372fd6.json
SET SHEET_ID=1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA

REM Run batch processing
python batch_process_brands.py --credentials "%CREDENTIALS%" --sheet-id "%SHEET_ID%" --delay 5

echo.
echo ============================================================
echo Processing Complete!
echo پردازش تکمیل شد!
echo ============================================================
echo.
pause
