BuildFlow ERP System Documentation
===================================

BuildFlow is a comprehensive ERP system specifically designed for construction and handcraft businesses.
It streamlines business operations from customer management to accounting with an intuitive web interface and guided workflow.

Features
--------

* **Customer Management** - Private and commercial customers with complete contact information
* **Order Management** - Detailed orders with material and labor components, project tracking
* **Invoice Generation** - Automatic PDF invoice creation with professional formatting
* **Payment Tracking** - Invoice payment status, dates, and receipt uploads
* **Expense Management** - Material cost recording with receipt uploads and manual bookings
* **Accounting (EÜR)** - German tax-compliant income-expense calculation with PDF reports
* **Dashboard & Analytics** - Business overview with revenue tracking and KPIs
* **Health Monitoring** - Production-ready monitoring and logging

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

Core Application
----------------

.. autosummary::
   :toctree: _autosummary

   app.main
   database.db

Data Models
-----------

.. autosummary::
   :toctree: _autosummary

   app.models.kunde
   app.models.auftrag
   app.models.rechnung
   app.models.material_komponente
   app.models.arbeit_komponente
   app.models.unternehmensdaten
   app.models.einnahme_ausgabe
   app.models.eur_kategorie

API Routes
----------

.. autosummary::
   :toctree: _autosummary

   app.routes.dashboard_route
   app.routes.kunde_route
   app.routes.auftrag_route
   app.routes.rechnung_route
   app.routes.buchungen
   app.routes.unternehmensdaten_route
   app.routes.startseite_route
   app.routes.auftrag_loeschen
   app.routes.health

Utilities
---------

.. autosummary::
   :toctree: _autosummary

   app.utils.file_validation
   app.utils.form_validation
   app.utils.logging_config
