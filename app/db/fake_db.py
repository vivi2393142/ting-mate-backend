# TODO: replace with real database in the future

from app.schemas.user import UserDB

# TODO: replace with real database

user1_id = "635acc4a-9dd4-44e1-b0f1-f86bd12b6e63"
user2_id = "b3157ca3-aa4d-4b7e-8a1f-972412be6b40"

fake_users_db = {
    # Registered user
    user1_id: UserDB(
        id=user1_id,
        email="user@example.com",
        hashed_password="$2b$12$7RSQMLM65WDMPFBezvITx.TOp4If6TrMNyvGscxBuwvu7bigFEsUK",  # noqa: E501
        anonymous_id=None,
    ),
    # Anonymous user
    user2_id: UserDB(
        id=user2_id,
        email=None,
        hashed_password=None,
        anonymous_id="anon_abc123",
    ),
}
