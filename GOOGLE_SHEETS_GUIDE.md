# راهنمای پردازش دسته‌ای برندها از Google Sheets
# Google Sheets Batch Processing Guide

## نمای کلی (Overview)

این سیستم به شما امکان می‌دهد که برندها را از یک Google Sheet بخوانید و به صورت خودکار برای هر برند گزارش جامع 9 فایله تولید کنید.

## پیش‌نیازها (Prerequisites)

### 1. اطلاعات Google Service Account

✅ شما در حال حاضر این موارد را دارید:
- **Service Account Email**: `test-867@claude-agents-487515.iam.gserviceaccount.com`
- **JSON Key File**: `C:\Users\TrendAgency\Downloads\claude-agents-487515-27f459372fd6.json`
- **Google Sheet ID**: `1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA`

### 2. دسترسی به Google Sheet

مطمئن شوید که Google Sheet را با Service Account به اشتراک گذاشته‌اید:
1. باز کردن Google Sheet
2. کلیک روی دکمه "Share"
3. اضافه کردن ایمیل: `test-867@claude-agents-487515.iam.gserviceaccount.com`
4. دادن دسترسی "Viewer" یا "Editor" (Editor برای به‌روزرسانی وضعیت)

### 3. ساختار Google Sheet

Google Sheet شما باید دارای ستون‌های زیر باشد:

| ستون | نام | محتوا | الزامی |
|------|-----|-------|---------|
| A | Brand Name | نام برند | ✅ بله |
| B | Website | آدرس وبسایت | خیر |
| C | Parent Company | نام شرکت مادر | خیر |
| D | Status | وضعیت پردازش (سیستم پر می‌کند) | خیر |
| E-H | Output Paths | مسیر فایل‌های خروجی (سیستم پر می‌کند) | خیر |

**مثال:**

```
| Brand Name    | Website                         | Parent Company | Status          | TXT Path | JSON Path | CSV Path | MD Path |
|---------------|----------------------------------|----------------|-----------------|----------|-----------|----------|---------|
| Zar_Macaron   | https://www.zarmacaron.com/     | Zar_group      | ✓ تکمیل شد      | ...      | ...       | ...      | ...     |
| Tage          | https://tage.ir/                | Henkel_AG_Co   | در حال پردازش... |          |           |          |         |
```

## نحوه استفاده (Usage)

### روش 1: اجرای کامل (Process All Brands)

برای پردازش تمام برندهای موجود در Google Sheet:

```bash
python batch_process_brands.py \
  --credentials "C:\Users\TrendAgency\Downloads\claude-agents-487515-27f459372fd6.json" \
  --sheet-id "1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA"
```

### روش 2: با تنظیمات سفارشی

```bash
python batch_process_brands.py \
  --credentials "C:\Users\TrendAgency\Downloads\claude-agents-487515-27f459372fd6.json" \
  --sheet-id "1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA" \
  --worksheet "Sheet1" \
  --delay 10
```

**پارامترها:**
- `--credentials`: مسیر فایل JSON credentials (الزامی)
- `--sheet-id`: شناسه Google Sheet (الزامی)
- `--worksheet`: نام برگه worksheet (اختیاری، پیش‌فرض: اولین برگه)
- `--delay`: تاخیر بین پردازش هر برند به ثانیه (پیش‌فرض: 5)
- `--no-update`: عدم به‌روزرسانی Google Sheet با وضعیت و نتایج

## فرآیند پردازش (Processing Flow)

برای هر برند در Google Sheet:

1. ✅ **خواندن اطلاعات برند** از Sheet
2. ✅ **به‌روزرسانی وضعیت** به "در حال پردازش..."
3. ✅ **اجرای 6 Agent** (جمع‌آوری داده، روابط، دسته‌بندی، کاتالوگ محصول، بینش، قالب‌بندی)
4. ✅ **تولید 9 فایل خروجی**:
   - `1_aggregated_brand_report.txt` (تمام داده‌ها در یک فایل متنی)
   - `2_master_report.md` (گزارش جامع Markdown)
   - `3_relationship_map.json` (نقشه روابط شرکتی)
   - `4_categorization.json` (دسته‌بندی صنعت و محصول)
   - `5_tabular_data.csv` (داده‌های جدولی)
   - `6_insights_for_vectorization.txt` (بینش‌های آماده برای embedding)
   - `7_product_catalog.json` (کاتالوگ کامل محصولات)
   - `8_structured_data.json` (تمام داده‌های ساختاریافته)
   - `9_embedding_ready.txt` (داده‌های آماده vectorization)
5. ✅ **به‌روزرسانی Google Sheet** با وضعیت "✓ تکمیل شد" و مسیرهای فایل

## نمونه خروجی (Sample Output)

```
==============================================================
BATCH BRAND PROCESSING FROM GOOGLE SHEETS
==============================================================

[OK] Successfully authenticated with Google Sheets API
[OK] Opened spreadsheet: test
[OK] Reading from worksheet: Sheet1
[OK] Read 4 brands from sheet

Found 4 brands to process

==============================================================
Processing brand 1/4: Zar_Macaron
==============================================================
Website: https://www.zarmacaron.com/
Parent Company: Zar_group

Starting brand intelligence analysis for: Zar_Macaron
...
[OK] Workflow completed in 45.32 seconds
[OK] Brand processed successfully in 45.32 seconds
[OK] Updated status for row 2: ✓ تکمیل شد (45.3s)
[OK] Wrote output paths for row 2

Waiting 5 seconds before next brand...

==============================================================
Processing brand 2/4: Tage
==============================================================
...

==============================================================
BATCH PROCESSING SUMMARY
==============================================================

Total brands processed: 4
✓ Successful: 4
✗ Failed: 0

Total processing time: 180.45 seconds
Average time per brand: 45.11 seconds

==============================================================
```

## ساختار فایل‌های خروجی (Output Structure)

تمام فایل‌های خروجی در پوشه `output/` ذخیره می‌شوند:

```
output/
├── zarmacaron_20260215_073145/
│   ├── 1_aggregated_brand_report.txt
│   ├── 2_master_report.md
│   ├── 3_relationship_map.json
│   ├── 4_categorization.json
│   ├── 5_tabular_data.csv
│   ├── 6_insights_for_vectorization.txt
│   ├── 7_product_catalog.json
│   ├── 8_structured_data.json
│   └── 9_embedding_ready.txt
├── tage_20260215_073230/
│   └── ...
└── ...
```

## نکات مهم (Important Notes)

### 1. محدودیت‌های نرخ (Rate Limiting)
- سیستم به طور خودکار بین پردازش هر برند تاخیر ایجاد می‌کند (پیش‌فرض: 5 ثانیه)
- برای تعداد زیاد برندها، می‌توانید تاخیر را افزایش دهید: `--delay 10`

### 2. مدیریت خطا (Error Handling)
- اگر پردازش یک برند با خطا مواجه شود، سیستم به برند بعدی می‌رود
- خطاها در Google Sheet با علامت "✗ خطا" ثبت می‌شوند
- در انتهای پردازش، خلاصه‌ای از برندهای موفق و ناموفق نمایش داده می‌شود

### 3. داده‌های جامع (Comprehensive Data)
سیستم برای هر برند اطلاعات زیر را جمع‌آوری می‌کند:
- ✅ ساختار شرکتی (شرکت مادر، شرکت‌های زیرمجموعه، برندهای خواهر)
- ✅ دسته‌بندی صنعت (3 سطح: Broad → Mid → Core)
- ✅ کاتالوگ کامل محصولات (تمام داروها، محصولات، خدمات)
- ✅ روابط بازاریابی و توزیع
- ✅ بینش‌های استراتژیک تبلیغاتی
- ✅ داده‌های آماده برای Vectorization

### 4. پایگاه دانش (Knowledge Base)
سیستم از پایگاه‌های دانش زیر استفاده می‌کند:
- `data/golrang_brands_database.json` (گروه گلرنگ)
- `data/cinnagen_complete_catalog.json` (گروه سیناژن)
- `data/iranian_brands_knowledge.json` (اطلاعات برندهای ایرانی)

برای برندهای جدید، می‌توانید فایل‌های مشابه ایجاد کنید.

## عیب‌یابی (Troubleshooting)

### خطا: "Failed to authenticate with Google Sheets"
**راه‌حل:**
1. مطمئن شوید که فایل JSON credentials موجود است
2. بررسی کنید که Service Account فعال است
3. مطمئن شوید که API های Google Sheets و Drive فعال هستند

### خطا: "Permission denied"
**راه‌حل:**
1. Google Sheet را با Service Account Email به اشتراک بگذارید
2. دسترسی "Viewer" یا "Editor" بدهید

### خطا: "No brands found in sheet"
**راه‌حل:**
1. مطمئن شوید که ستون A دارای نام برند است
2. ردیف 1 باید Header باشد (از ردیف 2 شروع به خواندن می‌کند)
3. سلول‌های خالی نادیده گرفته می‌شوند

### خطا: "ANTHROPIC_API_KEY not configured"
**راه‌حل:**
1. فایل `.env` ایجاد کنید
2. کلید API Anthropic خود را اضافه کنید:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

## مثال کامل (Complete Example)

### 1. آماده‌سازی Google Sheet

```
A                | B                            | C                  | D        | E | F | G | H
Brand Name       | Website                      | Parent Company     | Status   | TXT | JSON | CSV | MD
Zar_Macaron      | https://www.zarmacaron.com/ | Zar_group          |          |   |   |   |
Tage             | https://tage.ir/            | Henkel_AG_Co       |          |   |   |   |
Orchid_Pharmed   | https://orchidpharmed.com/  | CinnaGen           |          |   |   |   |
```

### 2. اجرای دستور

```bash
cd D:\Trend\AGENTS\brand-intelligence-agent

python batch_process_brands.py \
  --credentials "C:\Users\TrendAgency\Downloads\claude-agents-487515-27f459372fd6.json" \
  --sheet-id "1PJ3jvnYNj33fyC_wkqCEImbJI_qYJdWVFm2QC-NdukA" \
  --delay 5
```

### 3. نتیجه در Google Sheet

```
A                | B                            | C                  | D                      | E                  | F                   | ...
Brand Name       | Website                      | Parent Company     | Status                 | TXT Path           | JSON Path           | ...
Zar_Macaron      | https://www.zarmacaron.com/ | Zar_group          | ✓ تکمیل شد (45.2s)    | output/zarmacaron... | output/zarmacaron... | ...
Tage             | https://tage.ir/            | Henkel_AG_Co       | ✓ تکمیل شد (42.8s)    | output/tage...      | output/tage...      | ...
Orchid_Pharmed   | https://orchidpharmed.com/  | CinnaGen           | ✓ تکمیل شد (48.1s)    | output/orchid...    | output/orchid...    | ...
```

## پشتیبانی (Support)

برای سؤالات یا مشکلات:
- بررسی لاگ‌های سیستم در console
- بررسی فایل‌های خروجی در پوشه `output/`
- بررسی وضعیت در Google Sheet

---

**نسخه سیستم**: Brand Intelligence Agent v2.0
**تاریخ به‌روزرسانی**: 2026-02-15
