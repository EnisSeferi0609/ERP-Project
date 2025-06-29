# ERP System for Construction Businesses

This project is a custom ERP system specifically developed for small businesses. It manages customers, orders, materials, labor, and invoices through a web interface. It contains fictional company data.

## Features

- **Customer Management**  
  Create, edit, and delete private and commercial customers

- **Order Management**  
  Create and link orders including address data and status

- **Material & Labor Components**  
  Record material usage and labor effort per order

- **Invoices**  
  Automatic invoice generation with PDF export

- **Dashboard & Statistics**  
  Overview of revenue, orders, and key business metrics (in progress)

## Technology Stack

- **Python** & **FastAPI** – Backend logic and API routing  
- **Jinja2** – Templating for HTML  
- **SQLite** – Local database
- **SQLAlchemy** – ORM for database access  
- **HTML/CSS** – User interface

## Local Setup
### With Conda (recommended)

1. Clone the repository

2. Create and activate the environment:  
   ```bash
   conda env create -f environment.yml
   conda activate erp_env
   ```
   
3. Create data base:
    ```bash
    python create_db.py
    ```
    
4. Start the server:
    ```bash
    uvicorn app.main:app --reload
    ```
    
5. Open in your browser:
   ```bash
   http://127.0.0.1:8000
   ```

### With Pip (alternative)

1. Clone the repository

2. Create and activate the environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate       # on Linux/macOS  
   venv\Scripts\activate        # on Windows
   ```

3. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
    
4. Create data base:
    ```bash
    python create_db.py
    ```
    
5. Start the server:
    ```bash
    uvicorn app.main:app --reload
    ```
    
6. Open in your browser:
   ```bash
   http://127.0.0.1:8000
   ```
