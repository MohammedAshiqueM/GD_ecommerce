# 🛍️ GD_eCommerce
Grand Depart E-Commerce (GD_eCommerce) is a full-featured, scalable, backend-driven E-Commerce platform built with Django and PostgreSQL. It’s designed to support multiple product categories, dynamic product variants, and modern payment and authentication options — providing a flexible foundation for robust online retail experiences.

# 📌 Tech Stack
✅ Backend: Django (Python), PostgreSQL

✅ Frontend: Django Template Language (DTL), HTML, CSS, Bootstrap, JavaScript

✅ Payments: Razorpay integration, Wallet payments

✅ Authentication: Google OAuth, OTP-based Authentication

✅ Tools & Libraries:

  - Django Admin with custom dashboard

  - Sales Analytics using charts

  - PDF & Excel report generation

# 🚀 Features
# 🛒 User-Facing Features
✅ Main Categories & Subcategories: Organize products into multiple categories and subcategories.

✅ Product Variants: Supports scalable, Amazon/Flipkart-style product variant management.

✅ Secure Authentication:

- Email/password signup & login

- OTP-based verification

- Google Authentication via OAuth

✅ Payment Integration:

- Razorpay for online payments

- Wallet system for storing credits

✅ Order Management: Users can place, track, and manage orders easily.

✅ Responsive Frontend: Built using Django Templates with Bootstrap for mobile-friendly, clean interfaces.

# 🛠️ Admin Panel Features

✅ Sales Dashboard: Charts & analytics for tracking sales and order trends.

✅ Product & Category Management: Full CRUD for categories, subcategories, product variants, and stock.

✅ Order Management: View, update, or cancel orders.

✅ Reports:

- Generate PDF reports for sales

- Export Excel reports for order history and stock details

# 📂 Project Structure

```
GD_ecommerce/
│
├── Admin_side/               # Custom admin panel functionalities
│   ├── templates/
│   └── views.py
│
├── User_side/                # User-facing functionalities
│   ├── templates/
│   └── views.py
│
├── Grand_depart/             # Django project settings, URLs, WSGI, ASGI
│
├── ecommerce_venv/           # Python virtual environment
├── media/                    # Uploaded images and media files
├── db.sqlite3 (if fallback)  # SQLite (PostgreSQL used in production)
│
├── manage.py                 # Django project manager
├── requirements.txt          # Python package requirements
└── .gitignore                # Git ignored files list
```

# ⚙️ Setup Instructions

Clone the repository

```
git clone https://github.com/MohammedAshiqueM/GD_ecommerce.git
cd GD_ecommerce
```

Create & activate virtual environment

```
python -m venv ecommerce_venv
source ecommerce_venv/bin/activate   # Mac/Linux
ecommerce_venv\Scripts\activate      # Windows
```

Install dependencies

```
pip install -r requirements.txt
```

Configure PostgreSQL Database

Update settings.py with your PostgreSQL credentials.

Apply migrations

```
python manage.py migrate
```

Create superuser

```
python manage.py createsuperuser
```

Run development server

```
python manage.py runserver
```

Access the app

User side: http://localhost:8000/

Admin side: http://localhost:8000/dashboard/

# 📊 Schema Highlights

Flexible Product Schema

Products can belong to multiple categories and subcategories.

Each product can have multiple variants  independently.

Variant combinations and pricing handled dynamically.

User Wallet

Wallet table maintains user balances and transaction logs.

Order Schema

Links users, products, payment status, Razorpay transaction IDs, and wallet adjustments.

# 🙌 Credits & Thanks

Built by Mohammed Ashique

Tested and reviewed by industrial experts and Brocamp peers.
