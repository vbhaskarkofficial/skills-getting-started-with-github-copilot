from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_state(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activity_state):
    return TestClient(app_module.app)


def signup_url(activity_name):
    encoded_name = quote(activity_name, safe="")
    return f"/activities/{encoded_name}/signup"


def test_get_activities_returns_activity_data(client, activity_state):
    # Arrange
    expected_activities = activity_state

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"
    initial_participants = activity_state[activity_name]["participants"].copy()

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activity_state[activity_name]["participants"] == initial_participants + [email]


def test_duplicate_signup_returns_400_without_mutating_participants(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = activity_state[activity_name]["participants"][0]
    initial_participants = activity_state[activity_name]["participants"].copy()

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activity_state[activity_name]["participants"] == initial_participants


def test_signup_for_unknown_activity_returns_404(client, activity_state):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"
    initial_activities = deepcopy(activity_state)

    # Act
    response = client.post(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_state == initial_activities


def test_signup_without_email_returns_422(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    initial_activities = deepcopy(activity_state)

    # Act
    response = client.post(signup_url(activity_name))

    # Assert
    assert response.status_code == 422
    assert activity_state == initial_activities


def test_unregister_removes_participant(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = activity_state[activity_name]["participants"][0]
    remaining_participants = activity_state[activity_name]["participants"][1:]

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert activity_state[activity_name]["participants"] == remaining_participants


def test_unregister_missing_participant_returns_404(client, activity_state):
    # Arrange
    activity_name = "Chess Club"
    email = "not-signed-up@mergington.edu"
    initial_participants = activity_state[activity_name]["participants"].copy()

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity_state[activity_name]["participants"] == initial_participants


def test_unregister_from_unknown_activity_returns_404(client, activity_state):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"
    initial_activities = deepcopy(activity_state)

    # Act
    response = client.delete(signup_url(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_state == initial_activities