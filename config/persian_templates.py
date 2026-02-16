"""Persian text templates for output generation."""

PERSIAN_TEXTS = {
    # Master Report Headers
    "master_report_title": "گزارش جامع هوشمند برند",
    "brand": "برند",
    "generated": "تاریخ تولید",
    "report_id": "شناسه گزارش",

    # Section Titles
    "section_executive_summary": "بخش ۱: خلاصه اجرایی",
    "section_brand_profile": "بخش ۲: پروفایل برند",
    "section_corporate_structure": "بخش ۳: ساختار شرکتی و روابط",
    "section_market_categorization": "بخش ۴: دسته‌بندی بازار",
    "section_strategic_insights": "بخش ۵: بینش‌ها و فرصت‌های استراتژیک",
    "section_campaign_timing": "بخش ۶: توصیه‌های زمان‌بندی کمپین",
    "section_budget_channels": "بخش ۷: بودجه و کانال‌های توصیه‌شده",
    "section_creative_direction": "بخش ۸: جهت‌گیری خلاقیت",
    "section_success_metrics": "بخش ۹: معیارهای موفقیت و شاخص‌های کلیدی",

    # Field Labels
    "brand_name": "نام برند",
    "website": "وبسایت",
    "website_title": "عنوان وبسایت",
    "description": "توضیحات",
    "parent_company": "شرکت مادر",
    "ultimate_parent": "شرکت مادر نهایی",
    "stock_symbol": "نماد بورس",
    "industry": "صنعت",
    "market_cap": "ارزش بازار",
    "total_brands": "تعداد کل برندها",
    "sister_brands": "برندهای خواهر",
    "business_model": "مدل کسب‌وکار",
    "price_tier": "سطح قیمتی",
    "target_audiences": "مخاطبان هدف",
    "distribution_channels": "کانال‌های توزیع",

    # Strategic Insights
    "cross_promotion_opportunities": "فرصت‌های تبلیغات متقابل",
    "partner_brand": "برند شریک",
    "synergy_level": "سطح هم‌افزایی",
    "priority": "اولویت",
    "budget": "بودجه",
    "concept": "مفهوم کمپین",
    "target_audience": "مخاطب هدف",
    "expected_benefit": "منافع مورد انتظار",
    "implementation_difficulty": "سختی اجرا",

    # Campaign Timing
    "optimal_periods": "دوره‌های بهینه",
    "avoid_periods": "دوره‌های اجتناب",
    "quarterly_recommendations": "توصیه‌های فصلی",
    "seasonal_considerations": "ملاحظات فصلی",

    # Budget & Channels
    "estimated_budget": "بودجه تخمینی",
    "usd_equivalent": "معادل دلار",
    "channel_allocation": "تخصیص کانال",
    "channel_details": "جزئیات کانال‌ها",
    "rationale": "دلیل",
    "content_type": "نوع محتوا",

    # Creative Direction
    "key_messages": "پیام‌های کلیدی",
    "tone_and_style": "لحن و سبک",
    "visual_recommendations": "توصیه‌های بصری",
    "cultural_considerations": "ملاحظات فرهنگی",
    "hashtag_strategy": "استراتژی هشتگ",
    "content_themes": "تم‌های محتوایی",

    # Success Metrics
    "primary_kpis": "شاخص‌های کلیدی اصلی",
    "measurement_approach": "رویکرد اندازه‌گیری",
    "benchmarks": "معیارهای مقایسه",

    # Common Phrases
    "n_a": "نامشخص",
    "unknown": "نامشخص",
    "not_available": "در دسترس نیست",
    "in_progress": "در حال انجام",
    "completed": "تکمیل شده",
    "high": "بالا",
    "medium": "متوسط",
    "low": "پایین",
    "very_high": "بسیار بالا",

    # File Names
    "master_report_filename": "۰_گزارش_جامع",
    "brand_profile_filename": "۱_پروفایل_برند",
    "strategic_insights_filename": "۲_بینش_استراتژیک",
    "brands_database_filename": "۳_پایگاه_برندها",
    "embedding_ready_filename": "۴_متن_آماده_embedding",
    "financial_intelligence_filename": "۵_هوشمندی_مالی",
    "executive_summary_filename": "۶_خلاصه_اجرایی",
    "all_data_aggregated_filename": "۷_تجمیع_تمام_داده‌ها",
}

# Longer text templates
PERSIAN_LONG_TEXTS = {
    "no_executive_summary": "خلاصه اجرایی در دسترس نیست.",

    "company_structure_intro": "ساختار شرکتی {brand_name} نشان‌دهنده یک سلسله‌مراتب پیچیده از مالکیت و مدیریت برند است.",

    "subsidiary_benefits": """به عنوان یک شرکت تابعه مستقیم {parent}، این برند از مزایای زیر بهره‌مند است:
- پشتیبانی مالی و ثبات
- شبکه‌های توزیع مستقر
- تخصص عملیاتی و بهترین شیوه‌ها
- دسترسی به زیرساخت بازار {industry}""",

    "brand_family_intro": "{brand_name} بخشی از خانواده‌ای متشکل از {count} برند خواهر تحت شرکت مادر یکسان است.",

    "cross_promo_intro": "این برندهای خواهر فرصت‌های قابل توجهی برای تبلیغات متقابل و بازاریابی یکپارچه ایجاد می‌کنند:",

    "market_positioning_intro": "{brand_name} با مدل کسب‌وکار {business_model} فعالیت می‌کند و به {target} هدف‌گذاری می‌کند.",

    "price_tier_positioning": "برند در سطح قیمتی {tier} قرار دارد و بین کیفیت و مقرون‌به‌صرفه بودن تعادل ایجاد می‌کند.",

    "strategic_analysis_intro": "تحلیل استراتژیک {brand_name} نشان‌دهنده {count} فرصت با پتانسیل بالا برای تبلیغات متقابل با برندهای خواهر تحت {parent} است.",

    "primary_recommendation": "توصیه اصلی: استفاده از هم‌افزایی برند خانوادگی از طریق کمپین‌های یکپارچه با هدف خانواده‌های شهری ایرانی.",

    "digital_focus": "تمرکز بر اینستاگرام و تلگرام برای تعامل دیجیتال، همراه با تلویزیون سنتی برای آگاهی‌بخشی گسترده.",

    "budget_estimate": "بودجه تخمینی کمپین: {amount} برای رویکرد چندکاناله جامع.",

    "end_of_report": "پایان گزارش",
}
