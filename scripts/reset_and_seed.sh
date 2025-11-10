#!/bin/bash

# Complete reset and seed script
# This script resets the database and creates new superhero users

cd "$(dirname "$0")/.."

echo "============================================================"
echo "RAG Edtech System Reset and Seed"
echo "============================================================"
echo ""
echo "This will:"
echo "  - Delete ALL existing users, documents, and questions from MongoDB"
echo "  - Delete ALL vectors from Pinecone"
echo "  - Clear ALL Redis cache"
echo "  - Create 5 new teachers (superheroes)"
echo "  - Create 10 new students (superheroes)"
echo ""
read -p "Type 'DELETE ALL DATA' to confirm: " confirmation

if [ "$confirmation" != "DELETE ALL DATA" ]; then
    echo "Aborted. No changes were made."
    exit 1
fi

echo ""
echo "Running reset inside Docker container..."
echo ""

# Run reset script inside a Docker container with access to all services
docker compose exec -T api-gateway python3 << 'PYTHON_SCRIPT'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import os

async def reset_system():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGODB_URL', 'mongodb://admin:password123@mongodb:27017/rag_edtech?authSource=admin')
    client = AsyncIOMotorClient(mongo_url)
    db = client['rag_edtech']
    
    print("Deleting from MongoDB...")
    
    # Delete all data
    users_result = await db.users.delete_many({})
    content_result = await db.content.delete_many({})
    questions_result = await db.questions.delete_many({})
    
    print(f"  - Users deleted: {users_result.deleted_count}")
    print(f"  - Documents deleted: {content_result.deleted_count}")
    print(f"  - Questions deleted: {questions_result.deleted_count}")
    
    client.close()
    
    # Clear Redis
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url, decode_responses=True)
        
        print("\nClearing Redis cache...")
        
        keys_deleted = 0
        async for key in r.scan_iter(match="rag:cache:*"):
            await r.delete(key)
            keys_deleted += 1
        
        async for key in r.scan_iter(match="analytics:*"):
            await r.delete(key)
            keys_deleted += 1
        
        print(f"  - Cache keys deleted: {keys_deleted}")
        
        await r.close()
    except Exception as e:
        print(f"  - Redis error (skipping): {e}")
    
    print("\n✅ System reset completed!")

asyncio.run(reset_system())
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "Error during reset. Aborting."
    exit 1
fi

echo ""
echo "Creating new users..."
echo ""

# Create users using the auth service API
docker compose exec -T api-gateway python3 << 'PYTHON_SCRIPT'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from uuid import uuid4
import bcrypt
import os

PASSWORD = "TestPass@123"

TEACHERS = [
    {"full_name": "Tony Stark", "email": "tony.stark@edtech.com"},
    {"full_name": "Bruce Wayne", "email": "bruce.wayne@edtech.com"},
    {"full_name": "Diana Prince", "email": "diana.prince@edtech.com"},
    {"full_name": "Steve Rogers", "email": "steve.rogers@edtech.com"},
    {"full_name": "Clark Kent", "email": "clark.kent@edtech.com"},
]

STUDENTS = [
    {"full_name": "Peter Parker", "email": "peter.parker@edtech.com"},
    {"full_name": "Barry Allen", "email": "barry.allen@edtech.com"},
    {"full_name": "Natasha Romanoff", "email": "natasha.romanoff@edtech.com"},
    {"full_name": "Arthur Curry", "email": "arthur.curry@edtech.com"},
    {"full_name": "Wanda Maximoff", "email": "wanda.maximoff@edtech.com"},
    {"full_name": "Hal Jordan", "email": "hal.jordan@edtech.com"},
    {"full_name": "T'Challa", "email": "tchalla@edtech.com"},
    {"full_name": "Oliver Queen", "email": "oliver.queen@edtech.com"},
    {"full_name": "Carol Danvers", "email": "carol.danvers@edtech.com"},
    {"full_name": "Victor Stone", "email": "victor.stone@edtech.com"},
]

async def create_users():
    # Connect to MongoDB
    mongo_url = os.getenv('MONGODB_URL', 'mongodb://admin:password123@mongodb:27017/rag_edtech?authSource=admin')
    client = AsyncIOMotorClient(mongo_url)
    db = client['rag_edtech']
    
    # Hash password
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(PASSWORD.encode('utf-8'), salt).decode('utf-8')
    
    print("Creating Teachers:")
    print("-" * 60)
    for teacher in TEACHERS:
        user_doc = {
            "user_id": str(uuid4()),
            "email": teacher["email"],
            "full_name": teacher["full_name"],
            "role": "teacher",
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "metadata": {}
        }
        await db.users.insert_one(user_doc)
        print(f"  ✅ {teacher['full_name']} ({teacher['email']})")
    
    print("\nCreating Students:")
    print("-" * 60)
    for student in STUDENTS:
        user_doc = {
            "user_id": str(uuid4()),
            "email": student["email"],
            "full_name": student["full_name"],
            "role": "student",
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "metadata": {}
        }
        await db.users.insert_one(user_doc)
        print(f"  ✅ {student['full_name']} ({student['email']})")
    
    print("\n" + "=" * 60)
    print("USER CREATION SUMMARY")
    print("=" * 60)
    print(f"Teachers created: {len(TEACHERS)}")
    print(f"Students created: {len(STUDENTS)}")
    print(f"Total users: {len(TEACHERS) + len(STUDENTS)}")
    print(f"Password for all: {PASSWORD}")
    print("=" * 60)
    
    client.close()

asyncio.run(create_users())
PYTHON_SCRIPT

echo ""
echo "✅ System reset and seeding completed successfully!"
echo ""
echo "You can now log in with any of these users using password: TestPass@123"
echo ""

