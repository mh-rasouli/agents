"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return project root path."""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir(project_root_path):
    """Return test data directory."""
    test_dir = project_root_path / "tests" / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def sample_html():
    """Return sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>تست برند - صفحه اصلی</title>
        <meta name="description" content="توضیحات تست برند">
        <meta name="keywords" content="تست, برند, ایران">
        <meta property="og:title" content="تست برند">
    </head>
    <body>
        <header>
            <nav>
                <a href="/">خانه</a>
                <a href="/about-us">درباره ما</a>
                <a href="/contact">تماس با ما</a>
            </nav>
        </header>

        <main>
            <h1>خوش آمدید به تست برند</h1>
            <h2>محصولات ما</h2>
            <p>ما بهترین محصولات را ارائه می‌دهیم.</p>

            <section id="contact">
                <h3>تماس با ما</h3>
                <p>ایمیل: info@testbrand.ir</p>
                <p>تلفن: 021-12345678</p>
                <p>آدرس: تهران، خیابان ولیعصر</p>
            </section>

            <section id="social">
                <a href="https://instagram.com/testbrand">Instagram</a>
                <a href="https://t.me/testbrand">Telegram</a>
                <a href="https://linkedin.com/company/testbrand">LinkedIn</a>
            </section>
        </main>

        <footer>
            <p>تمامی حقوق محفوظ است © 2024</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_brand_data():
    """Return sample brand data for testing."""
    return {
        "brand_name": "تست برند",
        "brand_website": "https://testbrand.ir",
        "structured_data": {
            "legal_name_fa": "شرکت تست برند",
            "legal_name_en": "Test Brand Company",
            "industry": "تجارت الکترونیک",
            "revenue": 1000000000,
            "employees": 50
        },
        "relationships": {
            "parent_company": {"name": "شرکت مادر"},
            "subsidiaries": [
                {"name": "شرکت فرعی 1"},
                {"name": "شرکت فرعی 2"}
            ]
        },
        "categorization": {
            "primary_industry": {
                "name_fa": "تجارت الکترونیک",
                "name_en": "E-commerce"
            },
            "business_model": "B2C",
            "price_tier": "mid-market"
        }
    }
