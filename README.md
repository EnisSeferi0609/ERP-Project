# BuildFlow ERP System

BuildFlow is a comprehensive ERP system specifically designed for construction and handcraft businesses. It streamlines business operations from customer management to accounting with an intuitive web interface and guided workflow.

## Features

- **Customer Management**
  Create and manage private and commercial customers with complete contact information

- **Order Management**
  Create detailed orders with material and labor components, track project addresses and status

- **Invoice Generation**
  Automatic PDF invoice creation from orders with professional formatting

- **Payment Tracking**
  Mark invoices as paid, set payment dates, and track receipt uploads for materials

- **Expense Management**
  Record material costs with receipt uploads and manual booking entries

- **Accounting (EÜR)**
  Complete German tax-compliant income-expense calculation with PDF reports, timeline view, and yearly comparisons

- **Dashboard & Analytics**
  Business overview with revenue tracking and key performance metrics

- **Guided Workflow**
  Step-by-step process guidance from customer creation to bookkeeping

## Technology Stack

- **Backend**: Python with FastAPI framework
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML/CSS with Jinja2 templating
- **PDF Generation**: wkhtmltopdf for invoices and reports
- **File Handling**: Receipt uploads and document management
- **Architecture**: Component-based CSS structure with modular design
- **Testing**: pytest with automated test suite
- **Monitoring**: Health checks and structured logging
- **Production**: Error handling, environment configuration

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

## Testing

Run the test suite to verify everything works:

```bash
python -m pytest tests/ -v
```

## Health Monitoring

Check application health:

```bash
curl http://127.0.0.1:8000/health
```

## Documentation

- **API Documentation**: Generate with `cd doc && make html` (requires Sphinx)
- **Database Schema**: View with `sqlite3 erp.db ".schema"`
- **ER Diagram**: `er_diagram.pdf`
- **API Health Check**: `/health` endpoint
- **Logs**: Check `logs/buildflow.log` for application logs
