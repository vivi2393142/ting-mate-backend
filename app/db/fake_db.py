# TODO: replace with real database in the future

from app.schemas.user import User

fake_users_db = {
    "user@example.com": User(
        email="user@example.com",
        hashed_password="$2b$12$7RSQMLM65WDMPFBezvITx.TOp4If6TrMNyvGscxBuwvu7bigFEsUK",
    )
}
