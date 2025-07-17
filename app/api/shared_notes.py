from typing import List

from fastapi import Depends, HTTPException, Path

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import delete_route, get_route, post_route, put_route
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.shared_notes import SharedNotesRepository
from app.repositories.user import UserRepository
from app.schemas.user import (
    Role,
    SharedNote,
    SharedNoteCreate,
    SharedNoteUpdate,
    SharedNoteWithUser,
    User,
    UserInfo,
)


@get_route(
    path="/shared-notes",
    summary="Get Shared Notes",
    description=(
        "Get shared notes for the current user. For carereceivers, gets their own notes. "
        "For caregivers, gets the notes of their linked carereceivers."
    ),
    tags=["shared-notes"],
    response_model=List[SharedNoteWithUser],
)
def get_shared_notes_api(
    user: User = Depends(get_current_user_or_create_anonymous),
):
    try:
        if user.role == Role.CARERECEIVER:
            # Carereceiver gets their own notes
            notes = SharedNotesRepository.get_shared_notes_by_carereceiver_id(user.id)
        else:
            # Caregiver gets notes from their linked carereceivers
            notes = SharedNotesRepository.get_shared_notes_for_caregiver(user.id)
        # enrich created_by, updated_by
        enriched_notes = []
        for note in notes:
            created_user = UserRepository.get_user(note.created_by, "id")
            created_settings = UserRepository.get_user_settings(note.created_by)
            created_by = UserInfo(
                id=note.created_by,
                email=created_user.email if created_user else None,
                name=created_settings.get("name") if created_settings else None,
            )
            updated_user = UserRepository.get_user(note.updated_by, "id")
            updated_settings = UserRepository.get_user_settings(note.updated_by)
            updated_by = UserInfo(
                id=note.updated_by,
                email=updated_user.email if updated_user else None,
                name=updated_settings.get("name") if updated_settings else None,
            )
            enriched_notes.append(
                SharedNoteWithUser(
                    id=note.id,
                    carereceiver_id=note.carereceiver_id,
                    title=note.title,
                    content=note.content,
                    created_by=created_by,
                    updated_by=updated_by,
                    created_at=note.created_at,
                    updated_at=note.updated_at,
                )
            )
        return enriched_notes
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@post_route(
    path="/shared-notes",
    summary="Create Shared Note",
    description=(
        "Create a new shared note. Both caregivers and carereceivers can create notes, "
        "but they will be associated with the linked carereceiver."
    ),
    response_model=SharedNote,
    tags=["shared-notes"],
)
def create_shared_note_api(
    note_create: SharedNoteCreate,
    user: User = Depends(get_current_user_or_create_anonymous),
):
    try:
        # Determine the carereceiver_id for this note
        if user.role == Role.CARERECEIVER:
            carereceiver_id = user.id
        else:
            # Caregiver needs to find their linked carereceiver
            from app.repositories.user import UserRepository

            linked_carereceivers = UserRepository.get_linked_carereceivers(user.id)
            if not linked_carereceivers:
                raise HTTPException(
                    status_code=400,
                    detail="Caregiver must be linked to a carereceiver to create notes",
                )
            # Use the first linked carereceiver (you might want to add logic to choose specific one)
            carereceiver_id = linked_carereceivers[0]["id"]

        note = SharedNotesRepository.create_shared_note(
            carereceiver_id, note_create, user.id
        )

        if not note:
            raise HTTPException(status_code=400, detail="Failed to create shared note")

        # Log the shared note creation
        ActivityLogRepository.log_shared_note_create(
            user_id=user.id,
            target_user_id=carereceiver_id,
            note_title=note_create.title,
        )

        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@put_route(
    path="/shared-notes/{note_id}",
    summary="Update Shared Note",
    description=(
        "Update a specific shared note. Users can only update notes they have access to "
        "(own notes for carereceivers, linked carereceiver notes for caregivers)."
    ),
    response_model=SharedNote,
    tags=["shared-notes"],
)
def update_shared_note_api(
    note_update: SharedNoteUpdate,
    note_id: str = Path(..., description="The ID of the note to update"),
    user: User = Depends(get_current_user_or_create_anonymous),
):
    try:
        # Check if user can access this note
        if not SharedNotesRepository.can_user_access_note(
            user.id, note_id, user.role.value
        ):
            raise HTTPException(status_code=403, detail="Access denied to this note")

        # Get the original note for logging
        original_note = SharedNotesRepository.get_shared_note_by_id(note_id)
        if not original_note:
            raise HTTPException(status_code=404, detail="Shared note not found")

        updated_note = SharedNotesRepository.update_shared_note(
            note_id, note_update, user.id
        )

        if not updated_note:
            raise HTTPException(status_code=404, detail="Shared note not found")

        # Log the shared note update
        updated_fields = {}
        if note_update.title is not None:
            updated_fields["title"] = note_update.title
        if note_update.content is not None:
            updated_fields["content"] = note_update.content

        if updated_fields:
            ActivityLogRepository.log_shared_note_update(
                user_id=user.id,
                target_user_id=original_note.carereceiver_id,
                note_title=original_note.title,
                updated_fields=updated_fields,
            )

        return updated_note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@delete_route(
    path="/shared-notes/{note_id}",
    summary="Delete Shared Note",
    description=(
        "Delete a specific shared note. Users can only delete notes they have access to "
        "(own notes for carereceivers, linked carereceiver notes for caregivers)."
    ),
    tags=["shared-notes"],
)
def delete_shared_note_api(
    note_id: str = Path(..., description="The ID of the note to delete"),
    user: User = Depends(get_current_user_or_create_anonymous),
):
    try:
        # Check if user can access this note
        if not SharedNotesRepository.can_user_access_note(
            user.id, note_id, user.role.value
        ):
            raise HTTPException(status_code=403, detail="Access denied to this note")

        # Get the original note for logging
        original_note = SharedNotesRepository.get_shared_note_by_id(note_id)
        if not original_note:
            raise HTTPException(status_code=404, detail="Shared note not found")

        success = SharedNotesRepository.delete_shared_note(note_id)

        if not success:
            raise HTTPException(status_code=404, detail="Shared note not found")

        # Log the shared note deletion
        ActivityLogRepository.log_shared_note_delete(
            user_id=user.id,
            target_user_id=original_note.carereceiver_id,
            note_title=original_note.title,
        )

        return {"message": "Shared note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@get_route(
    path="/shared-notes/{note_id}",
    summary="Get Shared Note by ID",
    description="Get a single shared note by its ID, including user info.",
    tags=["shared-notes"],
    response_model=SharedNoteWithUser,
)
def get_shared_note_by_id_api(
    note_id: str = Path(..., description="The ID of the note to retrieve"),
    user: User = Depends(get_current_user_or_create_anonymous),
):
    try:
        # Check if user can access this note
        if not SharedNotesRepository.can_user_access_note(
            user.id, note_id, user.role.value
        ):
            raise HTTPException(status_code=403, detail="Access denied to this note")

        note = SharedNotesRepository.get_shared_note_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Shared note not found")

        created_user = UserRepository.get_user(note.created_by, "id")
        created_settings = UserRepository.get_user_settings(note.created_by)
        created_by = UserInfo(
            id=note.created_by,
            email=created_user.email if created_user else None,
            name=created_settings.get("name") if created_settings else None,
        )
        updated_user = UserRepository.get_user(note.updated_by, "id")
        updated_settings = UserRepository.get_user_settings(note.updated_by)
        updated_by = UserInfo(
            id=note.updated_by,
            email=updated_user.email if updated_user else None,
            name=updated_settings.get("name") if updated_settings else None,
        )
        return SharedNoteWithUser(
            id=note.id,
            carereceiver_id=note.carereceiver_id,
            title=note.title,
            content=note.content,
            created_by=created_by,
            updated_by=updated_by,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
