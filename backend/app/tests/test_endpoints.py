import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test: Create Comic

def test_create_comic():
    # Prepare a dummy PDF file in memory
    pdf_content = b"%PDF-1.4\n%Dummy PDF file\n"
    files = {
        "pdf": ("test.pdf", pdf_content, "application/pdf")
    }
    data = {
        "title": "Test Comic",
        "description": "A test comic.",
        "genres": "Action"
    }
    response = client.post("/comics/", data=data, files=files)
    assert response.status_code == 201
    assert "id" in response.json()

# Test: Get All Comics

def test_get_comics():
    response = client.get("/comics/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test: Get Comic by ID

def test_get_comic_by_id():
    data = {
        "title": "Test Comic 2",
        "description": "Another test comic.",
        "genres": "Action"
    }
    create_resp = client.post("/comics/", data=data)
    assert create_resp.status_code == 201
    comic_id = create_resp.json()["id"]
    response = client.get(f"/comics/{comic_id}")
    assert response.status_code == 200
    assert response.json()["id"] == comic_id

# Test: Update Comic

def test_update_comic():
    data = {
        "title": "Test Comic 3",
        "description": "Yet another test comic.",
        "genres": "Fantasy"
    }
    create_resp = client.post("/comics/", data=data)
    assert create_resp.status_code == 201
    comic_id = create_resp.json()["id"]
    response = client.put(f"/comics/{comic_id}", json={"title": "Updated Title", "description": "Updated description.", "genres": ["Fantasy"]})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

# Test: Delete Comic

def test_delete_comic():
    data = {
        "title": "Test Comic 4",
        "description": "Comic to be deleted.",
        "genres": "Horror"
    }
    create_resp = client.post("/comics/", data=data)
    assert create_resp.status_code == 201
    comic_id = create_resp.json()["id"]
    response = client.delete(f"/comics/{comic_id}")
    assert response.status_code == 204
