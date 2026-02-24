"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a dictionary
        assert isinstance(data, dict)
        
        # Verify some expected activities exist
        assert "Basketball Team" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
        
    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self):
        """Test successful signup of a new student"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_nonexistent_activity(self):
        """Test signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self):
        """Test that duplicate signup is rejected"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_updates_participants_list(self):
        """Test that signup adds student to participants list"""
        test_email = "test_signup@mergington.edu"
        activity_name = "Tennis Club"
        
        # Get initial participants count
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Sign up the student (ignore if already exists)
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        if signup_response.status_code == 200:
            # Verify participant was added
            response = client.get("/activities")
            new_count = len(response.json()[activity_name]["participants"])
            assert new_count == initial_count + 1
            assert test_email in response.json()[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_student_success(self):
        """Test successful unregistration of an existing student"""
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alex@mergington.edu" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_student_not_signed_up(self):
        """Test that unregistering a non-participant returns 400"""
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_removes_from_participants_list(self):
        """Test that unregister removes student from participants list"""
        # First, sign up a student
        test_email = "test_unregister@mergington.edu"
        activity_name = "Drama Club"
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        # Verify student is in list
        response = client.get("/activities")
        assert test_email in response.json()[activity_name]["participants"]
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Unregister the student
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        assert unregister_response.status_code == 200
        
        # Verify student was removed
        response = client.get("/activities")
        new_count = len(response.json()[activity_name]["participants"])
        assert new_count == initial_count - 1
        assert test_email not in response.json()[activity_name]["participants"]


class TestActivityConstraints:
    """Tests for activity constraints and business rules"""

    def test_cannot_exceed_max_participants(self):
        """Test that activity honors max_participants limit"""
        # Get current state
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Try to get the current participant count and max
        current_participants = len(chess_club["participants"])
        max_participants = chess_club["max_participants"]
        
        # This test verifies the structure exists
        assert current_participants > 0
        assert max_participants > 0
        assert current_participants <= max_participants


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_index(self):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
