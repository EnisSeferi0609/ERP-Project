# BuildFlow ERP System

BuildFlow is a comprehensive ERP system specifically designed for construction and handcraft businesses. It streamlines business operations from customer management to accounting with an intuitive web interface, guided workflow, and secure authentication.

## Quick Start

1. **Clone and install:**
   ```bash
   git clone <repo-url>
   cd ERP-Projekt

   # Create conda environment (recommended)
   conda create -n erp_env python=3.11
   conda activate erp_env
   conda install -c conda-forge weasyprint
   pip install -r requirements.txt

   # OR use pip only (may require system dependencies)
   # pip install -r requirements.txt

   python scripts/create_db.py
   ```

2. **Run locally:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **First setup:** Visit `http://localhost:8000/setup` to create your admin account

## Project Structure

```
├── app/                     # Main application
│   ├── models/             # Database models
│   ├── routes/             # API routes
│   ├── templates/          # HTML templates
│   └── utils/              # Utilities & auth
├── deployment/             # Production deployment
│   ├── docker/            # Docker & docker-compose
│   └── nginx/             # Nginx configuration
├── docs/                  # Documentation
├── scripts/               # Database & utility scripts
├── static/                # CSS, images, assets
└── tests/                 # Test files
```

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

### System Dependencies

Before installing Python dependencies, you need to install system libraries required by WeasyPrint for PDF generation:

**macOS (using Homebrew):**
```bash
brew install pango glib cairo gdk-pixbuf libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install pango-devel cairo-devel
# or for newer versions:
sudo dnf install pango-devel cairo-devel
```

### With Conda (recommended)

1. Clone the repository

2. Install system dependencies (see above)

3. Create and activate the environment:  
   ```bash
   conda env create -f docs/environment.yml
   conda activate erp_env
   ```
   
3. Create data base:
    ```bash
    python scripts/create_db.py
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

2. Install system dependencies (see above)

3. Create and activate the environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate       # on Linux/macOS  
   venv\Scripts\activate        # on Windows
   ```

4. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
    
5. Create data base:
    ```bash
    python scripts/create_db.py
    ```
    
6. Start the server:
    ```bash
    uvicorn app.main:app --reload
    ```
    
7. Open in your browser:
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
