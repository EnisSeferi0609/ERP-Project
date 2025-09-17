import pytest
from app.models.kunde import Kunde

def test_homepage(client):
    """Test homepage loads correctly"""
    response = client.get("/")
    assert response.status_code == 200
    assert "BuildFlow" in response.text

def test_dashboard(client):
    """Test dashboard loads"""
    response = client.get("/dashboard")
    assert response.status_code == 200

def test_kunde_model(test_db):
    """Test basic customer model"""
    kunde = Kunde(
        kunde_vorname="Test",
        kunde_nachname="User",
        kunde_email="test@example.com",
        kunde_telefon="0123456789",
        kundenart="Privatkunde"
    )

    test_db.add(kunde)
    test_db.commit()

    assert kunde.id is not None
    assert kunde.kunde_vorname == "Test"
    assert kunde.kunde_email == "test@example.com"

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data