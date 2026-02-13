import pytest


class TestActivitiesEndpoints:
    """Test the /activities endpoint"""

    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball" in data
        assert "Soccer" in data
        assert "Chess Club" in data
        
        # Verify activity structure
        basketball = data["Basketball"]
        assert basketball["description"] == "Team basketball practice and competitive games"
        assert basketball["schedule"] == "Mondays and Wednesdays, 4:00 PM - 5:30 PM"
        assert basketball["max_participants"] == 15
        assert isinstance(basketball["participants"], list)
        assert "alex@mergington.edu" in basketball["participants"]

    def test_get_activities_has_expected_count(self, client, reset_activities):
        """Test that we have the expected number of activities"""
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9  # 9 activities in total


class TestSignupEndpoints:
    """Test the signup functionality"""

    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify the participant was actually added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Basketball"]["participants"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_activity(self, client, reset_activities):
        """Test signing up for multiple activities (should fail)"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Soccer/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_already_participant(self, client, reset_activities):
        """Test signing up when already a participant"""
        # alex@mergington.edu is already in Basketball
        response = client.post(
            "/activities/Basketball/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]


class TestRemoveParticipantEndpoints:
    """Test the remove participant functionality"""

    def test_remove_participant_success(self, client, reset_activities):
        """Test successfully removing a participant"""
        # First verify alex is in Basketball
        activities_response = client.get("/activities")
        assert "alex@mergington.edu" in activities_response.json()["Basketball"]["participants"]
        
        # Remove the participant
        response = client.delete(
            "/activities/Basketball/participant/alex@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        
        # Verify the participant was actually removed
        activities_response = client.get("/activities")
        assert "alex@mergington.edu" not in activities_response.json()["Basketball"]["participants"]

    def test_remove_participant_nonexistent_activity(self, client, reset_activities):
        """Test removing a participant from a non-existent activity"""
        response = client.delete(
            "/activities/NonexistentActivity/participant/student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_remove_nonexistent_participant(self, client, reset_activities):
        """Test removing a participant that doesn't exist"""
        response = client.delete(
            "/activities/Basketball/participant/nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_then_signup_again(self, client, reset_activities):
        """Test that a removed participant can sign up for another activity"""
        # Remove alex from Basketball
        client.delete("/activities/Basketball/participant/alex@mergington.edu")
        
        # alex should now be able to sign up for Soccer
        response = client.post(
            "/activities/Soccer/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify alex is in Soccer but not in Basketball
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alex@mergington.edu" not in activities_data["Basketball"]["participants"]
        assert "alex@mergington.edu" in activities_data["Soccer"]["participants"]


class TestActivityCapacity:
    """Test activity capacity constraints"""

    def test_new_signup_affects_availability(self, client, reset_activities):
        """Test that new signups reduce available spots"""
        # Get initial availability for Basketball
        response1 = client.get("/activities")
        initial_participants = len(response1.json()["Basketball"]["participants"])
        initial_max = response1.json()["Basketball"]["max_participants"]
        initial_available = initial_max - initial_participants
        
        # Sign up a new student
        client.post("/activities/Basketball/signup?email=newone@mergington.edu")
        
        # Check updated availability
        response2 = client.get("/activities")
        new_participants = len(response2.json()["Basketball"]["participants"])
        new_available = initial_max - new_participants
        
        assert new_participants == initial_participants + 1
        assert new_available == initial_available - 1

    def test_participant_counts_accurate(self, client, reset_activities):
        """Test that participant counts are accurate across activities"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants
        assert len(activities["Chess Club"]["participants"]) == 2
        
        # Programming Class should have 2 participants
        assert len(activities["Programming Class"]["participants"]) == 2
        
        # Basketball should have 1 participant
        assert len(activities["Basketball"]["participants"]) == 1
