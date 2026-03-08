"""
Test suite for the Mergington High School API
Tests all endpoints using AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that the root endpoint redirects to /static/index.html"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to root
        response = client.get("/", follow_redirects=False)
        
        # Assert: Check redirect status and location
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self):
        """Test retrieving all activities"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to activities
        response = client.get("/activities")
        
        # Assert: Check response status and content
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_get_activities_returns_correct_structure(self):
        """Test that each activity has the required fields"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to activities
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert: Check structure of each activity
        for activity_name, activity_info in activities_data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_get_activities_has_initial_participants(self):
        """Test that some activities have initial participants"""
        # Arrange: No special setup needed
        
        # Act: Make GET request to activities
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert: Check initial participants in Chess Club
        chess_participants = activities_data["Chess Club"]["participants"]
        assert len(chess_participants) >= 2
        assert "michael@mergington.edu" in chess_participants


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self):
        """Test successful signup for an available activity"""
        # Arrange: Prepare test data
        activity = "Basketball Team"
        email = "newstudent@mergington.edu"
        
        # Act: Make POST request to signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: Check response and message
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_activity_not_found(self):
        """Test signup for a non-existent activity"""
        # Arrange: Use invalid activity name
        invalid_activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act: Make POST request to signup
        response = client.post(f"/activities/{invalid_activity}/signup?email={email}")
        
        # Assert: Check 404 error
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_student(self):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange: Sign up first time
        activity = "Chess Club"
        email = "duplicate@mergington.edu"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act: Attempt duplicate signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: Check 400 error for duplicate
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_multiple_students_signup(self):
        """Test that multiple students can sign up for the same activity"""
        # Arrange: Prepare multiple emails
        activity = "Tennis Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act: Sign up each student
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Assert: Verify all students are signed up
        response = client.get("/activities")
        tennis_participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in tennis_participants
    
    def test_signup_missing_email_parameter(self):
        """Test signup without email parameter"""
        # Arrange: Prepare request without email
        activity = "Chess Club"
        
        # Act: Make POST request without email
        response = client.post(f"/activities/{activity}/signup")
        
        # Assert: Check 422 validation error
        assert response.status_code == 422


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self):
        """Test successful unregistration from an activity"""
        # Arrange: Sign up first
        activity = "Art Studio"
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act: Make DELETE request to unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: Check success response
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_activity_not_found(self):
        """Test unregister from a non-existent activity"""
        # Arrange: Use invalid activity
        invalid_activity = "Fake Activity"
        email = "student@mergington.edu"
        
        # Act: Make DELETE request
        response = client.delete(f"/activities/{invalid_activity}/unregister?email={email}")
        
        # Assert: Check 404 error
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_student_not_signed_up(self):
        """Test unregister when student is not signed up"""
        # Arrange: Use activity and email not signed up
        activity = "Music Band"
        email = "notstudent@mergington.edu"
        
        # Act: Make DELETE request
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: Check 400 error
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_removes_participant(self):
        """Test that unregistration removes the participant"""
        # Arrange: Sign up first
        activity = "Robotics Club"
        email = "remove_test@mergington.edu"
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act: Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: Verify removal
        response = client.get("/activities")
        robotics_participants = response.json()[activity]["participants"]
        assert email not in robotics_participants
    
    def test_unregister_missing_email_parameter(self):
        """Test unregister without email parameter"""
        # Arrange: Prepare request without email
        activity = "Chess Club"
        
        # Act: Make DELETE request without email
        response = client.delete(f"/activities/{activity}/unregister")
        
        # Assert: Check 422 validation error
        assert response.status_code == 422


class TestEndToEndScenarios:
    """Integration tests for complete user workflows"""
    
    def test_full_signup_and_unregister_flow(self):
        """Test signing up and then unregistering from an activity"""
        # Arrange: Prepare test data
        activity = "Debate Team"
        email = "debate_student@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Act: Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: Signup successful
        assert signup_response.status_code == 200
        
        # Verify signup increased participant count
        response = client.get("/activities")
        after_signup_count = len(response.json()[activity]["participants"])
        assert after_signup_count == initial_count + 1
        
        # Act: Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: Unregister successful
        assert unregister_response.status_code == 200
        
        # Verify unregister decreased participant count
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count
    
    def test_multiple_activity_signups(self):
        """Test a student signing up for multiple activities"""
        # Arrange: Prepare test data
        email = "multi_student@mergington.edu"
        activities_list = ["Gym Class", "Programming Class"]
        
        # Act: Sign up for each activity
        for activity in activities_list:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Assert: Verify student is in both activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities_list:
            assert email in data[activity]["participants"]