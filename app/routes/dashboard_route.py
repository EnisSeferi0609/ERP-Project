"""Dashboard analytics and overview page with business metrics."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from collections import defaultdict
import calendar

from database.db import get_db
from app.models.kunde import Kunde
from app.models.auftrag import Auftrag
from app.models.rechnung import Rechnung
from app.models.einnahme_ausgabe import EinnahmeAusgabe
from app.models.material_komponente import MaterialKomponente
from app.models.arbeit_komponente import ArbeitKomponente
from app.utils.template_utils import create_templates

router = APIRouter()
templates = create_templates()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, year: int = None, db: Session = Depends(get_db)):
    """Business intelligence dashboard with key metrics and charts."""
    
    # Default to current year if none specified
    current_year = year or date.today().year
    
    # === KEY METRICS ===
    # Customer metrics
    total_customers = db.query(Kunde).count()
    private_customers = db.query(Kunde).filter(Kunde.kundenart == "Privatkunde").count()
    business_customers = db.query(Kunde).filter(Kunde.kundenart == "Geschäftskunde").count()
    
    # Order metrics
    total_orders = db.query(Auftrag).count()
    current_year_orders = db.query(Auftrag).filter(
        extract('year', Auftrag.auftrag_start) == current_year
    ).count()
    
    # Invoice metrics
    total_invoices = db.query(Rechnung).count()
    paid_invoices = db.query(Rechnung).filter(Rechnung.bezahlt == True).count()
    unpaid_invoices = db.query(Rechnung).filter(Rechnung.bezahlt == False).count()
    
    # Revenue calculations (current year)
    year_revenue = db.query(func.sum(Rechnung.rechnungssumme_gesamt)).filter(
        Rechnung.bezahlt == True,
        extract('year', Rechnung.payment_date) == current_year
    ).scalar() or 0
    
    # Expense calculations (current year)
    year_expenses = db.query(func.sum(EinnahmeAusgabe.betrag)).filter(
        EinnahmeAusgabe.typ == 'ausgabe',
        extract('year', EinnahmeAusgabe.datum) == current_year
    ).scalar() or 0
    
    # Profit calculation
    year_profit = year_revenue - year_expenses
    profit_margin = (year_profit / year_revenue * 100) if year_revenue > 0 else 0
    
    # === MONTHLY DATA FOR CHARTS ===
    # Monthly revenue data
    monthly_revenue = db.query(
        extract('month', Rechnung.payment_date).label('month'),
        func.sum(Rechnung.rechnungssumme_gesamt).label('revenue')
    ).filter(
        Rechnung.bezahlt == True,
        extract('year', Rechnung.payment_date) == current_year
    ).group_by(extract('month', Rechnung.payment_date)).all()
    
    # Monthly expense data
    monthly_expenses = db.query(
        extract('month', EinnahmeAusgabe.datum).label('month'),
        func.sum(EinnahmeAusgabe.betrag).label('expenses')
    ).filter(
        EinnahmeAusgabe.typ == 'ausgabe',
        extract('year', EinnahmeAusgabe.datum) == current_year
    ).group_by(extract('month', EinnahmeAusgabe.datum)).all()
    
    # Create 12-month arrays for charts
    months = [calendar.month_abbr[i] for i in range(1, 13)]
    revenue_data = [0] * 12
    expense_data = [0] * 12
    
    # Fill revenue data
    for month, revenue in monthly_revenue:
        if month and 1 <= month <= 12:
            revenue_data[int(month) - 1] = float(revenue or 0)
    
    # Fill expense data
    for month, expenses in monthly_expenses:
        if month and 1 <= month <= 12:
            expense_data[int(month) - 1] = float(expenses or 0)
    
    # Calculate profit data
    profit_data = [revenue_data[i] - expense_data[i] for i in range(12)]
    
    # === MATERIAL VS LABOR ANALYSIS ===
    # Get material costs vs labor costs for completed jobs (simplified for performance)
    material_costs = db.query(func.coalesce(func.sum(MaterialKomponente.actual_cost), 0)).filter(
        MaterialKomponente.actual_cost > 0
    ).scalar()
    
    # Simplified labor calculation
    labor_hours = db.query(func.coalesce(func.sum(
        ArbeitKomponente.anzahl_stunden * ArbeitKomponente.stundenlohn
    ), 0)).filter(
        ArbeitKomponente.anzahl_stunden.isnot(None),
        ArbeitKomponente.stundenlohn.isnot(None)
    ).scalar()
    
    labor_area = db.query(func.coalesce(func.sum(
        ArbeitKomponente.anzahl_quadrat * ArbeitKomponente.preis_pro_quadrat
    ), 0)).filter(
        ArbeitKomponente.anzahl_quadrat.isnot(None),
        ArbeitKomponente.preis_pro_quadrat.isnot(None)
    ).scalar()
    
    labor_revenue = labor_hours + labor_area
    
    # === RECENT ACTIVITY ===
    recent_invoices = db.query(Rechnung).order_by(Rechnung.id.desc()).limit(3).all()
    recent_bookings = db.query(EinnahmeAusgabe).filter(
        EinnahmeAusgabe.rechnung_id.is_(None)
    ).order_by(EinnahmeAusgabe.datum.desc()).limit(3).all()
    
    # === BUSINESS DEVELOPMENT DATA ===
    # Monthly customer registrations
    monthly_customers = db.query(
        extract('month', Kunde.kunde_seit).label('month'),
        func.count(Kunde.id).label('customers')
    ).filter(
        extract('year', Kunde.kunde_seit) == current_year
    ).group_by(extract('month', Kunde.kunde_seit)).all()
    
    # Monthly orders
    monthly_orders = db.query(
        extract('month', Auftrag.auftrag_start).label('month'),
        func.count(Auftrag.id).label('orders')
    ).filter(
        extract('year', Auftrag.auftrag_start) == current_year
    ).group_by(extract('month', Auftrag.auftrag_start)).all()
    
    # Monthly invoices
    monthly_invoices = db.query(
        extract('month', Rechnung.rechnungsdatum).label('month'),
        func.count(Rechnung.id).label('invoices')
    ).filter(
        extract('year', Rechnung.rechnungsdatum) == current_year
    ).group_by(extract('month', Rechnung.rechnungsdatum)).all()
    
    # Create 12-month arrays for business chart
    customers_data = [0] * 12
    orders_data = [0] * 12
    invoices_data = [0] * 12
    
    # Fill customer data
    for month, customers in monthly_customers:
        if month and 1 <= month <= 12:
            customers_data[int(month) - 1] = int(customers or 0)
    
    # Fill order data
    for month, orders in monthly_orders:
        if month and 1 <= month <= 12:
            orders_data[int(month) - 1] = int(orders or 0)
    
    # Fill invoice data
    for month, invoices in monthly_invoices:
        if month and 1 <= month <= 12:
            invoices_data[int(month) - 1] = int(invoices or 0)

    # === AVAILABLE YEARS FOR SELECTOR ===
    available_years = []
    
    # Get years from invoices
    invoice_years = db.query(extract('year', Rechnung.payment_date)).filter(
        Rechnung.payment_date.isnot(None)
    ).distinct().all()
    
    # Get years from bookings
    booking_years = db.query(extract('year', EinnahmeAusgabe.datum)).distinct().all()
    
    # Combine and sort years
    all_years = set()
    for (year_val,) in invoice_years + booking_years:
        if year_val:
            all_years.add(int(year_val))
    
    available_years = sorted(all_years, reverse=True)
    if not available_years:
        available_years = [date.today().year]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_year": current_year,
        "available_years": available_years,
        
        # Key metrics
        "total_customers": total_customers,
        "private_customers": private_customers,
        "business_customers": business_customers,
        "total_orders": total_orders,
        "current_year_orders": current_year_orders,
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "unpaid_invoices": unpaid_invoices,
        
        # Financial metrics
        "year_revenue": year_revenue,
        "year_expenses": year_expenses,
        "year_profit": year_profit,
        "profit_margin": profit_margin,
        
        # Chart data
        "months": months,
        "revenue_data": revenue_data,
        "expense_data": expense_data,
        "profit_data": profit_data,
        
        # Cost analysis
        "material_costs": material_costs,
        "labor_revenue": labor_revenue,
        
        # Recent activity
        "recent_invoices": recent_invoices,
        "recent_bookings": recent_bookings,
        
        # Business development data
        "customers_data": customers_data,
        "orders_data": orders_data,
        "invoices_data": invoices_data,
    })