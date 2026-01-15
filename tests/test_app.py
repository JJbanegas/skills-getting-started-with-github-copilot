"""
Test suite for Mergington High School Activities API

Tests cover endpoints for retrieving activities, signing up for activities,
and unregistering from activities.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the Python path to import the app module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original activities
    original_activities = {
        key: {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy()
        }
        for key, value in activities.items()
    }
    
    yield
    
    # Reset to original state after test
    for key in activities:
        activities[key]["participants"] = original_activities[key]["participants"].copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that activity details are included in response"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that participants list is included"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert isinstance(chess_club["participants"], list)
        assert len(chess_club["participants"]) > 0


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        email = "new_student@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify student was added
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signup for an activity when already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "multi_student@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify student is in both
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Verify student is registered
        assert email in activities["Chess Club"]["participants"]
        
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify student was removed
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister when student is not registered"""
        email = "not_registered@mergington.edu"
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up after unregistering"""
        email = "test_student@mergington.edu"
        
        # Sign up
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        response2 = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        assert email not in activities["Chess Club"]["participants"]
        
        # Sign up again
        response3 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        assert email in activities["Chess Club"]["participants"]


class TestActivityIntegration:
    """Integration tests for activity operations"""
    
    def test_activity_state_consistency(self, client, reset_activities):
        """Test that activity state remains consistent across operations"""
        response = client.get("/activities")
        initial_data = response.json()
        initial_participants = initial_data["Chess Club"]["participants"].copy()
        
        # Perform operations
        email = "integration_test@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        
        # Verify state
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == len(initial_participants) + 1
        assert email in data["Chess Club"]["participants"]
    
    def test_multiple_students_same_activity(self, client, reset_activities):
        """Test multiple students signing up for the same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        initial_count = len(activities["Tennis Club"]["participants"])
        
        for email in emails:
            response = client.post(
                "/activities/Tennis Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        assert len(activities["Tennis Club"]["participants"]) == initial_count + 3
        for email in emails:
            assert email in activities["Tennis Club"]["participants"]
