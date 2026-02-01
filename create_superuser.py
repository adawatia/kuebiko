import asyncio
import contextlib
from app.db import async_session_maker
from app.users import UserManager
from app.models import User
from fastapi_users.db import SQLAlchemyUserDatabase
from app.schemas import UserCreate

async def create_superuser():
    print("Create a Superuser for Comic Admin")
    print("----------------------------------")
    email = input("Enter superuser email: ")
    password = input("Enter superuser password: ")
    
    if not email or not password:
        print("Email and password are required.")
        return

    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)
        
        try:
            user = await user_manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_superuser=True,
                    is_active=True,
                    is_verified=True
                )
            )
            print(f"Superuser {user.email} created successfully!")
        except Exception as e:
            print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    asyncio.run(create_superuser())
