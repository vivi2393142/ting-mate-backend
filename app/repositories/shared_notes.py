"""
Shared Notes repository - handles all database operations for shared notes
"""

import uuid
from typing import List, Optional

from app.core.database import execute_query, execute_update
from app.schemas.user import Role, SharedNote, SharedNoteCreate, SharedNoteUpdate


class SharedNotesRepository:
    """Repository for shared notes data access operations"""

    @staticmethod
    def get_shared_notes_by_carereceiver_id(carereceiver_id: str) -> List[SharedNote]:
        """Get all shared notes for a specific carereceiver_id."""
        try:
            query = """
            SELECT id, carereceiver_id, title, content, created_by, updated_by, created_at, updated_at
            FROM shared_notes 
            WHERE carereceiver_id = %s
            ORDER BY updated_at DESC
            """
            result = execute_query(query, (carereceiver_id,))
            notes = []
            for note_data in result:
                notes.append(
                    SharedNote(
                        id=note_data["id"],
                        carereceiver_id=note_data["carereceiver_id"],
                        title=note_data["title"],
                        content=note_data["content"],
                        created_by=note_data["created_by"],
                        updated_by=note_data["updated_by"],
                        created_at=note_data["created_at"],
                        updated_at=note_data["updated_at"],
                    )
                )
            return notes
        except Exception as e:
            print(f"Error getting shared notes: {e}")
            return []

    @staticmethod
    def get_shared_notes_for_caregiver(caregiver_id: str) -> List[SharedNote]:
        """Get all shared notes for a caregiver by finding their linked carereceiver."""
        try:
            query = """
            SELECT sn.id, sn.carereceiver_id, sn.title, sn.content, 
                   sn.created_by, sn.updated_by, sn.created_at, sn.updated_at
            FROM shared_notes sn
            JOIN user_links ul ON sn.carereceiver_id = ul.carereceiver_id
            WHERE ul.caregiver_id = %s
            ORDER BY sn.updated_at DESC
            """
            result = execute_query(query, (caregiver_id,))
            notes = []
            for note_data in result:
                notes.append(
                    SharedNote(
                        id=note_data["id"],
                        carereceiver_id=note_data["carereceiver_id"],
                        title=note_data["title"],
                        content=note_data["content"],
                        created_by=note_data["created_by"],
                        updated_by=note_data["updated_by"],
                        created_at=note_data["created_at"],
                        updated_at=note_data["updated_at"],
                    )
                )
            return notes
        except Exception as e:
            print(f"Error getting shared notes for caregiver: {e}")
            return []

    @staticmethod
    def get_shared_note_by_id(note_id: str) -> Optional[SharedNote]:
        """Get a specific shared note by its ID."""
        try:
            query = """
            SELECT id, carereceiver_id, title, content, created_by, updated_by, created_at, updated_at
            FROM shared_notes 
            WHERE id = %s
            """
            result = execute_query(query, (note_id,))
            if result:
                note_data = result[0]
                return SharedNote(
                    id=note_data["id"],
                    carereceiver_id=note_data["carereceiver_id"],
                    title=note_data["title"],
                    content=note_data["content"],
                    created_by=note_data["created_by"],
                    updated_by=note_data["updated_by"],
                    created_at=note_data["created_at"],
                    updated_at=note_data["updated_at"],
                )
            return None
        except Exception as e:
            print(f"Error getting shared note by id: {e}")
            return None

    @staticmethod
    def create_shared_note(
        carereceiver_id: str, note_create: SharedNoteCreate, created_by: str
    ) -> Optional[SharedNote]:
        """Create a new shared note."""
        try:
            note_id = str(uuid.uuid4())
            insert_sql = """
            INSERT INTO shared_notes (id, carereceiver_id, title, content, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            execute_update(
                insert_sql,
                (
                    note_id,
                    carereceiver_id,
                    note_create.title,
                    note_create.content,
                    created_by,
                    created_by,
                ),
            )

            # Return the created note
            return SharedNotesRepository.get_shared_note_by_id(note_id)
        except Exception as e:
            print(f"Error creating shared note: {e}")
            return None

    @staticmethod
    def update_shared_note(
        note_id: str, note_update: SharedNoteUpdate, updated_by: str
    ) -> Optional[SharedNote]:
        """Update an existing shared note."""
        try:
            # Check if note exists
            existing_note = SharedNotesRepository.get_shared_note_by_id(note_id)
            if not existing_note:
                raise ValueError("Shared note not found")

            # Build dynamic update query
            update_fields = []
            update_values = []

            if note_update.title is not None:
                update_fields.append("title = %s")
                update_values.append(note_update.title)

            if note_update.content is not None:
                update_fields.append("content = %s")
                update_values.append(note_update.content)

            if not update_fields:
                # No fields to update
                return existing_note

            # Add updated_by and note_id to values
            update_fields.append("updated_by = %s")
            update_values.append(updated_by)
            update_values.append(note_id)

            # Construct the update query
            update_sql = f"""
            UPDATE shared_notes 
            SET {', '.join(update_fields)}
            WHERE id = %s
            """

            execute_update(update_sql, tuple(update_values))

            # Return the updated note
            return SharedNotesRepository.get_shared_note_by_id(note_id)
        except Exception as e:
            print(f"Error updating shared note: {e}")
            return None

    @staticmethod
    def delete_shared_note(note_id: str) -> bool:
        """Delete a shared note."""
        try:
            delete_sql = "DELETE FROM shared_notes WHERE id = %s"
            result = execute_update(delete_sql, (note_id,))
            return result > 0
        except Exception as e:
            print(f"Error deleting shared note: {e}")
            return False

    @staticmethod
    def delete_all_notes_for_carereceiver(carereceiver_id: str) -> bool:
        """Delete all notes for a specific carereceiver."""
        try:
            delete_sql = "DELETE FROM shared_notes WHERE carereceiver_id = %s"
            result = execute_update(delete_sql, (carereceiver_id,))
            return result >= 0  # Return True even if no notes were deleted
        except Exception as e:
            print(f"Error deleting notes for carereceiver: {e}")
            return False

    @staticmethod
    def delete_all_notes_created_by_user(user_id: str) -> bool:
        """Delete all notes created by a specific user."""
        try:
            delete_sql = "DELETE FROM shared_notes WHERE created_by = %s"
            result = execute_update(delete_sql, (user_id,))
            return result >= 0  # Return True even if no notes were deleted
        except Exception as e:
            print(f"Error deleting notes created by user: {e}")
            return False

    @staticmethod
    def can_user_access_note(user_id: str, note_id: str, user_role: str) -> bool:
        """Check if a user can access a specific note."""
        try:
            note = SharedNotesRepository.get_shared_note_by_id(note_id)
            if not note:
                return False

            # Carereceiver can access their own notes
            if user_role == Role.CARERECEIVER and note.carereceiver_id == user_id:
                return True

            # Caregiver can access notes of their linked carereceivers
            if user_role == Role.CAREGIVER:
                query = """
                SELECT 1 FROM user_links 
                WHERE caregiver_id = %s AND carereceiver_id = %s
                """
                result = execute_query(query, (user_id, note.carereceiver_id))
                return len(result) > 0

            return False
        except Exception as e:
            print(f"Error checking note access: {e}")
            return False
