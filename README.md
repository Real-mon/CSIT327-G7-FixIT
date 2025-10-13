# 🧰 FixIT - Computer Repair Service System

A **Django-based web application** that connects users with technicians to fix computer problems efficiently.

---

## 🚀 Features

- User authentication (Sign Up & Login)  
- User dashboard with account details  
- Technician hiring system  
- PostgreSQL database integration (Supabase)

---

## 🧠 Tech Stack

- **Backend:** Django 4.2+  
- **Database:** PostgreSQL (Supabase)  
- **Frontend:** HTML, CSS, JavaScript  
- **Framework:** Bootstrap 5  

---
## Team Members
💻 Sigrid Laputan - Frontend (UI & Tailwind Integration)​
⚙️ Andrae Lapis ​ – Backend & Supabase configuration
🧩 Justin Monreal ​– Dashboard & integration logic​

---
## ⚙️ Installation

### 🧾 Prerequisites

Make sure you have the following installed:

- **Python 3.8+**  
- **Git**  
- **Supabase account**

---

### 🪜 Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/fixit-django-system.git
cd fixit-django-system

# 2. Create a virtual environment
python -m venv env

# 3. Activate the virtual environment
# Windows
env\Scripts\activate
# macOS/Linux
source env/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
# Create a .env file in the project root and add your database credentials
# Example:
# DATABASE_URL=your_database_url
# SECRET_KEY=your_secret_key
# DEBUG=True

# 6. Run migrations
python manage.py migrate

# 7. Create a superuser
python manage.py createsuperuser

# 8. Run the development server
python manage.py runserver

# 9. Open your browser and go to
# http://127.0.0.1:8000








