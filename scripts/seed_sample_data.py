"""
Seed Sample Data Script
Generates realistic 1 week of activity data for 15 superhero users.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4
import random
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB configuration (hardcoded for seed script)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:SecurePassword123!@localhost:27017/?authSource=admin")
MONGODB_DATABASE = "rag_edtech"

print(f"Using MongoDB: {MONGODB_URL}")
print(f"Database: {MONGODB_DATABASE}")

# Sample subjects and topics
CHEMISTRY_TOPICS = [
    "Stoichiometry and Molar Calculations",
    "Atomic Structure and Periodicity",
    "Chemical Bonding and Structure",
    "Thermodynamics and Energetics",
    "Kinetics and Reaction Rates",
    "Equilibrium and Le Chatelier's Principle",
    "Acids and Bases",
    "Redox and Electrochemistry",
    "Organic Chemistry Fundamentals",
    "Analytical Techniques"
]

PHYSICS_TOPICS = [
    "Mechanics and Motion",
    "Forces and Energy",
    "Waves and Oscillations",
    "Electricity and Magnetism",
    "Thermodynamics",
    "Modern Physics and Quantum",
]

BIOLOGY_TOPICS = [
    "Cell Biology and Structure",
    "Genetics and Evolution",
    "Ecology and Ecosystems",
    "Human Physiology",
]

MATH_TOPICS = [
    "Calculus Fundamentals",
    "Linear Algebra",
    "Statistics and Probability",
    "Trigonometry",
]

# Question templates by subject
CHEMISTRY_QUESTIONS = [
    "What is the definition of {topic}?",
    "Explain how {topic} works",
    "How do I calculate {topic}?",
    "What are the key principles of {topic}?",
    "Compare {topic} with related concepts",
    "What are common mistakes in {topic}?",
    "Give me practice problems on {topic}",
    "How does {topic} apply to real-world scenarios?",
]

PHYSICS_QUESTIONS = [
    "Explain the physics behind {topic}",
    "How do I solve {topic} problems?",
    "What equations are used in {topic}?",
    "Derive the formula for {topic}",
    "What are the applications of {topic}?",
]

# Sample answers (will be replaced with real RAG answers in production)
SAMPLE_ANSWERS = {
    "chemistry": """Based on the provided educational materials, here's a comprehensive explanation:

This concept is fundamental to IB Chemistry and involves understanding the relationship between different chemical quantities. Let me break it down step by step:

**Key Concepts:**
1. The mole is the unit of amount of substance (Avogadro's number: 6.02 × 10²³)
2. Molar mass connects mass to moles
3. The balanced chemical equation shows mole ratios

**Calculation Steps:**
1. Write the balanced equation
2. Identify known and unknown quantities
3. Convert to moles if necessary
4. Use mole ratios from the equation
5. Convert back to desired units

**Common Mistakes:**
- Forgetting to balance the equation first
- Mixing up molar mass with molecular mass
- Not using correct significant figures

**Practice Tip:** Always start with dimensional analysis and check your units!

[Source 1: Referenced from uploaded chemistry materials]""",
    
    "physics": """From the physics principles covered in your materials:

**Fundamental Concepts:**
This topic involves the relationship between force, mass, and acceleration, described by Newton's Second Law: F = ma

**Key Equations:**
- F = ma (Newton's Second Law)
- Work: W = F·d·cos(θ)
- Kinetic Energy: KE = ½mv²

**Problem-Solving Approach:**
1. Draw a free-body diagram
2. Identify all forces
3. Choose a coordinate system
4. Apply Newton's laws
5. Solve algebraically before plugging in numbers

**Real-World Applications:**
- Vehicle dynamics
- Projectile motion
- Orbital mechanics

[Source 1: Referenced from physics materials]""",
    
    "biology": """According to the biological concepts in your study materials:

**Overview:**
This topic explores the fundamental processes of life at the cellular and molecular level.

**Key Points:**
1. Structure determines function
2. Energy transfer is essential
3. Regulation maintains homeostasis

**Experimental Context:**
- Microscopy techniques reveal cellular structures
- Biochemical assays measure activity
- Genetic analysis shows relationships

**Connections:**
- Links to evolution and adaptation
- Relates to ecology and ecosystems
- Applies to medical and biotechnological applications

[Source 1: Referenced from biology materials]""",
}


async def seed_all_data():
    """Main function to seed all sample data."""
    print("=" * 60)
    print("STARTING SAMPLE DATA SEEDING (1 WEEK)")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    
    print(f"Connected to MongoDB: {MONGODB_DATABASE}")
    
    try:
        # Get existing users
        users = await db.users.find({}).to_list(length=None)
        
        if len(users) < 15:
            print(f"ERROR: Need 15 users, found {len(users)}. Run create_users.py first!")
            return
        
        print(f"Found {len(users)} users")
        
        # Separate students and teachers
        students = [u for u in users if u.get('role') == 'student']
        teachers = [u for u in users if u.get('role') == 'teacher']
        
        print(f"Students: {len(students)}, Teachers: {len(teachers)}")
        
        # Generate documents for students
        print("\n📚 Generating documents...")
        documents = []
        
        # Each student uploads 1-3 documents
        for student in students[:10]:  # First 10 students
            num_docs = random.randint(1, 3)
            
            for _ in range(num_docs):
                subject = random.choice(['Chemistry', 'Physics', 'Biology', 'Mathematics'])
                topics = {
                    'Chemistry': CHEMISTRY_TOPICS,
                    'Physics': PHYSICS_TOPICS,
                    'Biology': BIOLOGY_TOPICS,
                    'Mathematics': MATH_TOPICS
                }[subject]
                
                topic = random.choice(topics)
                
                # Random upload date in past week
                days_ago = random.randint(1, 7)
                upload_date = datetime.utcnow() - timedelta(days=days_ago)
                
                doc = {
                    "content_id": str(uuid4()),
                    "filename": f"{topic.replace(' ', '_').lower()}.pdf",
                    "file_type": "pdf",
                    "user_id": student['user_id'],
                    "content_hash": str(uuid4()),  # Unique hash
                    "is_duplicate": False,
                    "original_uploader_id": student['user_id'],
                    "original_upload_date": upload_date,
                    "upload_history": [{
                        "user_id": student['user_id'],
                        "user_name": student['full_name'],
                        "upload_date": upload_date,
                        "filename": f"{topic}.pdf",
                        "content_hash": str(uuid4())
                    }],
                    "version_number": 1,
                    "status": "completed",
                    "total_chunks": random.randint(30, 80),
                    "processed_chunks": random.randint(30, 80),
                    "tags": topic.lower().split()[:3],
                    "metadata": {
                        "title": topic,
                        "subject": subject,
                        "uploader_name": student['full_name'],
                        "page_count": random.randint(10, 50),
                        "file_size": round(random.uniform(1.5, 5.0), 2)
                    },
                    "upload_date": upload_date,
                    "updated_at": upload_date
                }
                
                documents.append(doc)
        
        # Teachers upload 2-4 documents each
        for teacher in teachers[:3]:  # First 3 teachers
            num_docs = random.randint(2, 4)
            
            for _ in range(num_docs):
                subject = random.choice(['Chemistry', 'Physics'])
                topics = CHEMISTRY_TOPICS if subject == 'Chemistry' else PHYSICS_TOPICS
                topic = random.choice(topics)
                
                days_ago = random.randint(2, 7)
                upload_date = datetime.utcnow() - timedelta(days=days_ago)
                
                doc = {
                    "content_id": str(uuid4()),
                    "filename": f"{topic.replace(' ', '_').lower()}.pdf",
                    "file_type": "pdf",
                    "user_id": teacher['user_id'],
                    "content_hash": str(uuid4()),
                    "is_duplicate": False,
                    "original_uploader_id": teacher['user_id'],
                    "original_upload_date": upload_date,
                    "upload_history": [{
                        "user_id": teacher['user_id'],
                        "user_name": teacher['full_name'],
                        "upload_date": upload_date,
                        "filename": f"{topic}.pdf",
                        "content_hash": str(uuid4())
                    }],
                    "version_number": 1,
                    "status": "completed",
                    "total_chunks": random.randint(40, 100),
                    "processed_chunks": random.randint(40, 100),
                    "tags": topic.lower().split()[:3],
                    "metadata": {
                        "title": topic,
                        "subject": subject,
                        "uploader_name": teacher['full_name'],
                        "page_count": random.randint(20, 80),
                        "file_size": round(random.uniform(2.0, 8.0), 2)
                    },
                    "upload_date": upload_date,
                    "updated_at": upload_date
                }
                
                documents.append(doc)
        
        # Insert documents
        if documents:
            await db.content.insert_many(documents)
            print(f"✓ Inserted {len(documents)} documents")
        
        # Generate questions for each document
        print("\n💬 Generating questions...")
        questions = []
        
        for doc in documents:
            subject = doc['metadata']['subject']
            topic = doc['metadata']['title']
            
            # Each document gets 5-15 questions
            num_questions = random.randint(5, 15)
            
            # Pick random students to ask questions
            asking_students = random.sample(students, min(len(students), random.randint(1, 5)))
            
            for i in range(num_questions):
                student = random.choice(asking_students)
                
                # Generate question text
                if subject == 'Chemistry':
                    q_template = random.choice(CHEMISTRY_QUESTIONS)
                elif subject == 'Physics':
                    q_template = random.choice(PHYSICS_QUESTIONS)
                else:
                    q_template = "Explain {topic}"
                
                question_text = q_template.format(topic=topic)
                
                # Random timestamp in past week
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                created_at = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
                
                # Make sure question is after document upload
                if created_at < doc['upload_date']:
                    created_at = doc['upload_date'] + timedelta(hours=random.randint(1, 48))
                
                # Get answer for subject
                answer_text = SAMPLE_ANSWERS.get(subject.lower(), SAMPLE_ANSWERS['chemistry'])
                
                question = {
                    "question_id": str(uuid4()),
                    "content_id": doc['content_id'],
                    "session_id": str(uuid4()),
                    "student_id": student['user_id'],
                    "question_text": question_text,
                    "answer_text": answer_text,
                    "timestamp": created_at,
                    "created_at": created_at,  # Add both for compatibility
                    "response_time_ms": random.randint(1500, 3500),
                    "tokens_used": {
                        "prompt_tokens": random.randint(800, 1500),
                        "completion_tokens": random.randint(200, 500),
                        "total_tokens": random.randint(1000, 2000)
                    },
                    "cached": random.random() < 0.3,  # 30% cached
                    "question_type": random.choice(['definition', 'explanation', 'comparison', 'procedure', 'application']),
                    "classification_confidence": round(random.uniform(0.75, 0.95), 2),
                    "is_global": False,
                    "metadata": {
                        "subject": subject,
                        "grade_level": "IB Diploma"
                    }
                }
                
                questions.append(question)
        
        # Insert questions
        if questions:
            await db.questions.insert_many(questions)
            print(f"✓ Inserted {len(questions)} questions")
        
        # Generate suggested questions for each document
        print("\n💡 Generating suggested questions...")
        suggested_questions = []
        
        for doc in documents:
            subject = doc['metadata']['subject']
            topic = doc['metadata']['title']
            content_id = doc['content_id']
            
            # Generate 5 suggested questions per document
            suggestions = [
                {
                    "id": f"{content_id}-q1",
                    "question": f"What are the fundamental concepts in {topic}?",
                    "category": "definition",
                    "difficulty": "easy",
                    "content_id": content_id
                },
                {
                    "id": f"{content_id}-q2",
                    "question": f"Explain how {topic} works in detail",
                    "category": "explanation",
                    "difficulty": "medium",
                    "content_id": content_id
                },
                {
                    "id": f"{content_id}-q3",
                    "question": f"Compare {topic} with related concepts",
                    "category": "comparison",
                    "difficulty": "medium",
                    "content_id": content_id
                },
                {
                    "id": f"{content_id}-q4",
                    "question": f"Walk me through solving {topic} problems step-by-step",
                    "category": "procedure",
                    "difficulty": "hard",
                    "content_id": content_id
                },
                {
                    "id": f"{content_id}-q5",
                    "question": f"Apply {topic} to real-world examples",
                    "category": "application",
                    "difficulty": "hard",
                    "content_id": content_id
                }
            ]
            
            suggested_questions.extend(suggestions)
        
        # Insert suggested questions
        if suggested_questions:
            await db.suggested_questions.insert_many(suggested_questions)
            print(f"✓ Inserted {len(suggested_questions)} suggested questions")
        
        # Update last_activity for documents
        print("\n🔄 Updating last activity...")
        for doc in documents:
            doc_questions = [q for q in questions if q['content_id'] == doc['content_id']]
            if doc_questions:
                latest = max(doc_questions, key=lambda x: x['timestamp'])
                await db.content.update_one(
                    {"content_id": doc['content_id']},
                    {"$set": {"last_activity": latest['timestamp']}}
                )
        
        print("✓ Updated last activity timestamps")
        
        # Print summary statistics
        print("\n" + "=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print(f"📄 Documents created: {len(documents)}")
        print(f"❓ Questions generated: {len(questions)}")
        print(f"💡 Suggested questions: {len(suggested_questions)}")
        print(f"👥 Active students: {len(set(q['student_id'] for q in questions))}")
        print(f"📊 Avg questions per doc: {len(questions) // len(documents) if documents else 0}")
        print("=" * 60)
        
        # Print sample data
        print("\n📊 Sample Data Summary:")
        for subject in ['Chemistry', 'Physics', 'Biology', 'Mathematics']:
            subject_docs = [d for d in documents if d['metadata']['subject'] == subject]
            subject_qs = [q for q in questions if q['metadata']['subject'] == subject]
            if subject_docs:
                print(f"{subject}: {len(subject_docs)} docs, {len(subject_qs)} questions")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         RAG Edtech - Sample Data Seeding Script          ║
    ║                                                          ║
    ║  This will generate 1 week of realistic data:           ║
    ║  - ~30-40 documents across 4 subjects                   ║
    ║  - ~200-400 questions with answers                      ║
    ║  - ~150-200 suggested questions                         ║
    ║  - Activity from 15 superhero users                     ║
    ║                                                          ║
    ║  NOTE: Make sure users exist first!                     ║
    ║  Run: python scripts/create_users.py                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    confirm = input("Continue with seeding? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)
    
    asyncio.run(seed_all_data())
    print("\n✅ Seeding complete! Check your database.")

