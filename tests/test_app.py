"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint"""

    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Check that all required activities are present
        required_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Science Club"
        ]
        for activity in required_activities:
            assert activity in activities

    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newuser@mergington.edu"}
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newuser@mergington.edu" in result["message"]

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signups are rejected"""
        # First signup
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Attempt duplicate signup
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "user@mergington.edu"}
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]

    def test_signup_participant_appears_in_activity(self, client):
        """Test that signed-up participant appears in activity"""
        email = "testuser@mergington.edu"
        
        # Sign up
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant is in activity
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_participant(self, client):
        """Test unregistering a participant"""
        email = "unregister@mergington.edu"
        
        # First sign up
        client.post(
            "/activities/Art%20Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Art%20Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "user@mergington.edu"}
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]

    def test_unregister_not_registered_participant(self, client):
        """Test unregistering a participant who isn't signed up"""
        response = client.post(
            "/activities/Drama%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]

    def test_unregister_participant_removed_from_activity(self, client):
        """Test that unregistered participant is removed from activity"""
        email = "removal@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Debate%20Team/signup",
            params={"email": email}
        )
        
        # Unregister
        client.post(
            "/activities/Debate%20Team/unregister",
            params={"email": email}
        )
        
        # Verify participant is removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Debate Team"]["participants"]


class TestIntegration:
    """Integration tests for multiple operations"""

    def test_signup_and_unregister_flow(self, client):
        """Test complete signup and unregister flow"""
        email = "integration@mergington.edu"
        activity = "Science%20Club"
        
        # Get initial state
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before["Science Club"]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify participant added
        activities_after_signup = client.get("/activities").json()
        assert len(activities_after_signup["Science Club"]["participants"]) == initial_count + 1
        assert email in activities_after_signup["Science Club"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify participant removed
        activities_after_unregister = client.get("/activities").json()
        assert len(activities_after_unregister["Science Club"]["participants"]) == initial_count
        assert email not in activities_after_unregister["Science Club"]["participants"]

    def test_multiple_participants_signup(self, client):
        """Test multiple participants signing up for same activity"""
        activity = "Basketball%20Club"
        emails = [
            "multi1@mergington.edu",
            "multi2@mergington.edu",
            "multi3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all participants are added
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities["Basketball Club"]["participants"]
