"""
Tests for Shared Notes API
"""

import uuid

from fastapi import status

from app.schemas.user import Role
from tests.conftest import auth_headers


class TestSharedNotesAPI:
    """Test group for shared notes functionality."""

    def test_create_shared_note_carereceiver_success(self, client, register_user):
        """Success: carereceiver creates shared note."""
        email, token, _ = register_user(Role.CARERECEIVER)

        note_data = {"title": "Test Note", "content": "This is a test note content"}

        response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["title"] == "Test Note"
        assert data["content"] == "This is a test note content"
        assert "id" in data
        assert "carereceiver_id" in data
        assert "created_by" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_shared_note_caregiver_success(self, client, register_user):
        """Success: caregiver creates shared note for linked carereceiver."""
        # Create carereceiver first
        carereceiver_email, carereceiver_token, carereceiver_id = register_user(
            Role.CARERECEIVER
        )

        # Create caregiver and link them
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)

        # Generate invitation from carereceiver
        invite_response = client.post(
            "/user/invitations/generate", headers=auth_headers(carereceiver_token)
        )
        assert invite_response.status_code == status.HTTP_200_OK
        code = invite_response.json()["invitation_code"]

        # Caregiver accepts invitation
        accept_response = client.post(
            f"/user/invitations/{code}/accept", headers=auth_headers(caregiver_token)
        )
        assert accept_response.status_code == status.HTTP_200_OK

        # Caregiver creates a note
        note_data = {
            "title": "Caregiver Note",
            "content": "This is a note created by caregiver",
        }

        response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(caregiver_token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["title"] == "Caregiver Note"
        assert data["content"] == "This is a note created by caregiver"
        assert data["carereceiver_id"] == carereceiver_id

    def test_create_shared_note_caregiver_no_link_fail(self, client, register_user):
        """Fail: caregiver cannot create note without being linked to carereceiver."""
        email, token, _ = register_user(Role.CAREGIVER)

        note_data = {"title": "Test Note", "content": "This is a test note content"}

        response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_shared_note_carereceiver_no_link_success(
        self, client, register_user
    ):
        """Success: carereceiver can create note even without any links."""
        email, token, _ = register_user(Role.CARERECEIVER)

        note_data = {"title": "Test Note", "content": "This is a test note content"}

        response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["title"] == "Test Note"
        assert data["content"] == "This is a test note content"

    def test_get_shared_notes_carereceiver_success(self, client, register_user):
        """Success: carereceiver gets their own notes."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # First create a note
        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert create_response.status_code == status.HTTP_200_OK

        # Then get the notes
        get_response = client.get("/shared-notes", headers=auth_headers(token))
        assert get_response.status_code == status.HTTP_200_OK

        notes = get_response.json()
        assert isinstance(notes, list)
        assert len(notes) == 1
        note = notes[0]
        assert note["title"] == "Test Note"
        assert note["content"] == "This is a test note content"
        assert "created_by" in note
        assert "updated_by" in note
        assert isinstance(note["created_by"], dict)
        assert isinstance(note["updated_by"], dict)
        assert "id" in note["created_by"]
        assert "email" in note["created_by"]
        assert "name" in note["created_by"]
        assert "id" in note["updated_by"]
        assert "email" in note["updated_by"]
        assert "name" in note["updated_by"]

    def test_get_shared_notes_caregiver_success(self, client, register_user):
        """Success: caregiver gets linked carereceiver's notes."""
        # Create carereceiver and note
        carereceiver_email, carereceiver_token, carereceiver_id = register_user(
            Role.CARERECEIVER
        )

        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(carereceiver_token)
        )
        assert create_response.status_code == status.HTTP_200_OK

        # Create caregiver and link them
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)

        # Generate invitation from carereceiver
        invite_response = client.post(
            "/user/invitations/generate", headers=auth_headers(carereceiver_token)
        )
        assert invite_response.status_code == status.HTTP_200_OK
        code = invite_response.json()["invitation_code"]

        # Caregiver accepts invitation
        accept_response = client.post(
            f"/user/invitations/{code}/accept", headers=auth_headers(caregiver_token)
        )
        assert accept_response.status_code == status.HTTP_200_OK

        # Caregiver gets the shared notes
        get_response = client.get(
            "/shared-notes", headers=auth_headers(caregiver_token)
        )
        assert get_response.status_code == status.HTTP_200_OK

        notes = get_response.json()
        assert isinstance(notes, list)
        assert len(notes) == 1
        note = notes[0]
        assert note["title"] == "Test Note"
        assert note["content"] == "This is a test note content"
        assert note["carereceiver_id"] == carereceiver_id
        assert "created_by" in note
        assert "updated_by" in note
        assert isinstance(note["created_by"], dict)
        assert isinstance(note["updated_by"], dict)

    def test_get_shared_notes_empty(self, client, register_user):
        """Success: get notes when none exist."""
        email, token, _ = register_user(Role.CARERECEIVER)

        response = client.get("/shared-notes", headers=auth_headers(token))
        assert response.status_code == status.HTTP_200_OK
        notes = response.json()
        assert isinstance(notes, list)
        assert notes == []

    def test_update_shared_note_success(self, client, register_user):
        """Success: update shared note."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # First create a note
        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Then update the note
        update_data = {"title": "Updated Note", "content": "This is updated content"}
        update_response = client.put(
            f"/shared-notes/{note_id}", json=update_data, headers=auth_headers(token)
        )
        assert update_response.status_code == status.HTTP_200_OK

        data = update_response.json()
        assert data["title"] == "Updated Note"
        assert data["content"] == "This is updated content"

    def test_update_shared_note_partial(self, client, register_user):
        """Success: update only some fields."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # First create a note
        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Then update only title
        update_data = {"title": "Updated Note"}
        update_response = client.put(
            f"/shared-notes/{note_id}", json=update_data, headers=auth_headers(token)
        )
        assert update_response.status_code == status.HTTP_200_OK

        data = update_response.json()
        assert data["title"] == "Updated Note"
        assert data["content"] == "This is a test note content"  # Unchanged

    def test_update_shared_note_not_found(self, client, register_user):
        """Fail: update note when none exists."""
        email, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"title": "Updated Note"}
        fake_note_id = str(uuid.uuid4())
        response = client.put(
            f"/shared-notes/{fake_note_id}",
            json=update_data,
            headers=auth_headers(token),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_shared_note_unauthorized(self, client, register_user):
        """Fail: update note without access."""
        # Create carereceiver and note
        carereceiver_email, carereceiver_token, _ = register_user(Role.CARERECEIVER)

        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(carereceiver_token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Create another carereceiver who shouldn't have access
        other_email, other_token, _ = register_user(Role.CARERECEIVER)

        update_data = {"title": "Updated Note"}
        response = client.put(
            f"/shared-notes/{note_id}",
            json=update_data,
            headers=auth_headers(other_token),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_shared_note_success(self, client, register_user):
        """Success: delete shared note."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # First create a note
        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Then delete the note
        delete_response = client.delete(
            f"/shared-notes/{note_id}", headers=auth_headers(token)
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify note is deleted
        get_response = client.get("/shared-notes", headers=auth_headers(token))
        assert get_response.status_code == status.HTTP_200_OK
        notes = get_response.json()
        assert notes == []

    def test_delete_shared_note_unauthorized(self, client, register_user):
        """Fail: delete note without access."""
        # Create carereceiver and note
        carereceiver_email, carereceiver_token, _ = register_user(Role.CARERECEIVER)

        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(carereceiver_token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Create another carereceiver who shouldn't have access
        other_email, other_token, _ = register_user(Role.CARERECEIVER)

        response = client.delete(
            f"/shared-notes/{note_id}", headers=auth_headers(other_token)
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_shared_note_not_found(self, client, register_user):
        """Fail: delete note when none exists."""
        email, token, _ = register_user(Role.CARERECEIVER)

        fake_note_id = str(uuid.uuid4())
        response = client.delete(
            f"/shared-notes/{fake_note_id}", headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_caregiver_can_update_linked_note(self, client, register_user):
        """Success: caregiver can update linked carereceiver's note."""
        # Create carereceiver and note
        carereceiver_email, carereceiver_token, _ = register_user(Role.CARERECEIVER)

        note_data = {"title": "Test Note", "content": "This is a test note content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(carereceiver_token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Create caregiver and link them
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)

        # Generate invitation from carereceiver
        invite_response = client.post(
            "/user/invitations/generate", headers=auth_headers(carereceiver_token)
        )
        assert invite_response.status_code == status.HTTP_200_OK
        code = invite_response.json()["invitation_code"]

        # Caregiver accepts invitation
        accept_response = client.post(
            f"/user/invitations/{code}/accept", headers=auth_headers(caregiver_token)
        )
        assert accept_response.status_code == status.HTTP_200_OK

        # Caregiver updates the note
        update_data = {"title": "Updated by Caregiver"}
        update_response = client.put(
            f"/shared-notes/{note_id}",
            json=update_data,
            headers=auth_headers(caregiver_token),
        )
        assert update_response.status_code == status.HTTP_200_OK

        data = update_response.json()
        assert data["title"] == "Updated by Caregiver"

    def test_multiple_caregivers_edit_same_note(self, client, register_user):
        """Success: multiple caregivers can edit the same note and see updates."""
        # Create carereceiver and note
        carereceiver_email, carereceiver_token, carereceiver_id = register_user(
            Role.CARERECEIVER
        )

        note_data = {"title": "Shared Note", "content": "Original content"}
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(carereceiver_token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Create first caregiver and link them
        caregiver1_email, caregiver1_token, _ = register_user(Role.CAREGIVER)

        # Generate invitation from carereceiver
        invite_response = client.post(
            "/user/invitations/generate", headers=auth_headers(carereceiver_token)
        )
        assert invite_response.status_code == status.HTTP_200_OK
        code = invite_response.json()["invitation_code"]

        # First caregiver accepts invitation
        accept_response = client.post(
            f"/user/invitations/{code}/accept", headers=auth_headers(caregiver1_token)
        )
        assert accept_response.status_code == status.HTTP_200_OK

        # Create second caregiver and link them
        caregiver2_email, caregiver2_token, _ = register_user(Role.CAREGIVER)

        # Generate another invitation
        invite_response2 = client.post(
            "/user/invitations/generate", headers=auth_headers(carereceiver_token)
        )
        assert invite_response2.status_code == status.HTTP_200_OK
        code2 = invite_response2.json()["invitation_code"]

        # Second caregiver accepts invitation
        accept_response2 = client.post(
            f"/user/invitations/{code2}/accept", headers=auth_headers(caregiver2_token)
        )
        assert accept_response2.status_code == status.HTTP_200_OK

        # First caregiver edits the note
        update_data1 = {
            "title": "Updated by Caregiver 1",
            "content": "Content from caregiver 1",
        }
        update_response1 = client.put(
            f"/shared-notes/{note_id}",
            json=update_data1,
            headers=auth_headers(caregiver1_token),
        )
        assert update_response1.status_code == status.HTTP_200_OK

        # Second caregiver should see the updated note
        get_response2 = client.get(
            "/shared-notes", headers=auth_headers(caregiver2_token)
        )
        assert get_response2.status_code == status.HTTP_200_OK
        notes2 = get_response2.json()
        assert len(notes2) == 1
        assert notes2[0]["title"] == "Updated by Caregiver 1"
        assert notes2[0]["content"] == "Content from caregiver 1"

        # Second caregiver edits the note
        update_data2 = {"content": "Content from caregiver 2"}
        update_response2 = client.put(
            f"/shared-notes/{note_id}",
            json=update_data2,
            headers=auth_headers(caregiver2_token),
        )
        assert update_response2.status_code == status.HTTP_200_OK

        # First caregiver should see the updated note
        get_response1 = client.get(
            "/shared-notes", headers=auth_headers(caregiver1_token)
        )
        assert get_response1.status_code == status.HTTP_200_OK
        notes1 = get_response1.json()
        assert len(notes1) == 1
        assert notes1[0]["title"] == "Updated by Caregiver 1"  # Title unchanged
        assert notes1[0]["content"] == "Content from caregiver 2"  # Content updated

        # Carereceiver should also see the final updated note
        get_response_carereceiver = client.get(
            "/shared-notes", headers=auth_headers(carereceiver_token)
        )
        assert get_response_carereceiver.status_code == status.HTTP_200_OK
        notes_carereceiver = get_response_carereceiver.json()
        assert len(notes_carereceiver) == 1
        assert notes_carereceiver[0]["title"] == "Updated by Caregiver 1"
        assert notes_carereceiver[0]["content"] == "Content from caregiver 2"

    def test_role_transition_deletes_notes(self, client, register_user):
        """Success: when user transitions to carereceiver, their notes are deleted."""
        # Create a carereceiver first and create a note
        carereceiver_email, carereceiver_token, carereceiver_id = register_user(
            Role.CARERECEIVER
        )

        # Carereceiver creates a note
        note_data = {
            "title": "Carereceiver's Note",
            "content": "This note will be deleted when transitioning",
        }
        create_response = client.post(
            "/shared-notes", json=note_data, headers=auth_headers(carereceiver_token)
        )
        assert create_response.status_code == status.HTTP_200_OK
        note_id = create_response.json()["id"]

        # Verify the note exists
        get_response = client.get(
            "/shared-notes", headers=auth_headers(carereceiver_token)
        )
        assert get_response.status_code == status.HTTP_200_OK
        notes = get_response.json()
        assert len(notes) == 1
        assert notes[0]["id"] == note_id

        # Transition the carereceiver to caregiver role
        transition_data = {"target_role": "CAREGIVER"}
        transition_response = client.post(
            "/user/role/transition",
            json=transition_data,
            headers=auth_headers(carereceiver_token),
        )
        assert transition_response.status_code == status.HTTP_200_OK

        # Verify that the note is no longer accessible (should be deleted)
        get_response_after = client.get(
            "/shared-notes", headers=auth_headers(carereceiver_token)
        )
        assert get_response_after.status_code == status.HTTP_200_OK
        notes_after = get_response_after.json()
        assert notes_after == []  # Note should be deleted

        # Transition back to carereceiver to test the other direction
        transition_data_back = {"target_role": "CARERECEIVER"}
        transition_response_back = client.post(
            "/user/role/transition",
            json=transition_data_back,
            headers=auth_headers(carereceiver_token),
        )
        assert transition_response_back.status_code == status.HTTP_200_OK

        # Verify that after transitioning back, there are still no notes
        get_response_final = client.get(
            "/shared-notes", headers=auth_headers(carereceiver_token)
        )
        assert get_response_final.status_code == status.HTTP_200_OK
        notes_final = get_response_final.json()
        assert notes_final == []  # Notes should still be deleted
