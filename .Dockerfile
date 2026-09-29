# استفاده از پایتون نسخه سبک (Slim)
FROM python:3.11-slim

# تنظیم دایرکتوری کاری در کانتینر
WORKDIR /app

# نصب پکیج‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نصب مرورگر کرومیوم و تمام پکیج‌ها و کتابخانه‌های سیستمی Playwright در لینوکس
RUN playwright install --with-deps chromium

# کپی کردن کل کدهای پروژه به کانتینر
COPY . .

# اجرای فایل اصلی پایپ‌لاین
CMD ["python", "main.py"]