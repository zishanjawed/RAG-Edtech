"""
Vectorize Seeded Documents Script
Creates Pinecone vectors for documents that were added directly to MongoDB.
This enables chat functionality for test documents.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pinecone import Pinecone
from openai import AsyncOpenAI
import tiktoken

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:SecurePassword123!@localhost:27017/?authSource=admin")
MONGODB_DATABASE = "rag_edtech"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "edtech-rag-index")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Sample educational content by subject
SAMPLE_CONTENT = {
    "Chemistry": """# Chemistry Complete Notes

## Stoichiometry
Stoichiometry is the quantitative relationship between reactants and products in a chemical reaction. The mole is the fundamental unit (6.02 × 10²³ particles).

**Key Concepts:**
- Molar mass connects mass to moles
- Balanced equations show mole ratios
- Limiting reactant determines product amount

## Chemical Bonding
Covalent bonds form when atoms share electrons. Ionic bonds form when electrons transfer.

## Thermodynamics  
Enthalpy (ΔH) measures heat energy. Entropy (ΔS) measures disorder. Gibbs free energy (ΔG = ΔH - TΔS) predicts spontaneity.

## Acids and Bases
pH = -log[H+]. Strong acids completely dissociate. Weak acids partially dissociate. Buffers resist pH changes.

## Electrochemistry
Oxidation is loss of electrons. Reduction is gain of electrons. Galvanic cells convert chemical energy to electrical energy.""",

    "Physics": """# Physics Complete Notes

## Mechanics
Newton's Laws: F=ma. Work = F·d·cos(θ). Kinetic Energy = ½mv².

## Waves
Wave equation: v = fλ. Interference creates constructive and destructive patterns.

## Electricity
Ohm's Law: V=IR. Power: P=VI. Kirchhoff's laws for circuits.

## Thermodynamics
First Law: Energy is conserved. Second Law: Entropy increases.

## Modern Physics
E=mc². Photoelectric effect: E=hf. Wave-particle duality.""",

    "Biology": """# Biology Complete Notes

## Cell Biology
Cells are the basic unit of life. Prokaryotes lack nucleus. Eukaryotes have membrane-bound organelles.

## Genetics
DNA stores genetic information. RNA translates to proteins. Mendel's laws explain inheritance.

## Evolution
Natural selection drives adaptation. Genetic variation is the raw material. Fitness determines reproductive success.

## Ecology
Energy flows through trophic levels. Nutrients cycle. Carrying capacity limits population growth.""",

    "Mathematics": """# Mathematics Complete Notes

## Calculus
Derivative: rate of change. Integral: area under curve. Fundamental Theorem connects them.

## Algebra
Quadratic formula: x = (-b ± √(b²-4ac))/2a. Systems of equations have unique, infinite, or no solutions.

## Trigonometry
sin²θ + cos²θ = 1. Law of sines: a/sin(A) = b/sin(B). Law of cosines: c² = a² + b² - 2ab·cos(C).

## Statistics
Mean, median, mode. Standard deviation measures spread. Normal distribution: 68-95-99.7 rule."""
}


def chunk_text(text: str, max_tokens: int = 512, overlap: int = 50) -> list:
    """
    Chunk text into segments of max_tokens with overlap.
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Overlap tokens between chunks
    
    Returns:
        List of text chunks
    """
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += (max_tokens - overlap)
    
    return chunks


async def vectorize_documents():
    """Vectorize all seeded documents."""
    print("=" * 60)
    print("VECTORIZING SEEDED DOCUMENTS")
    print("=" * 60)
    
    if not PINECONE_API_KEY or not OPENAI_API_KEY:
        print("ERROR: PINECONE_API_KEY and OPENAI_API_KEY must be set!")
        print("Set them in your environment or .env file")
        return
    
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient(MONGODB_URL)
    db = mongo_client[MONGODB_DATABASE]
    
    # Connect to Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Initialize OpenAI
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    print(f"✓ Connected to MongoDB: {MONGODB_DATABASE}")
    print(f"✓ Connected to Pinecone: {PINECONE_INDEX_NAME}")
    print(f"✓ OpenAI client initialized")
    
    try:
        # Get all completed documents without checking Pinecone
        documents = await db.content.find({"status": "completed"}).to_list(length=None)
        
        print(f"\n📚 Found {len(documents)} documents to vectorize")
        
        total_vectors = 0
        
        for doc_num, doc in enumerate(documents, 1):
            content_id = doc['content_id']
            subject = doc.get('metadata', {}).get('subject', 'General')
            title = doc.get('metadata', {}).get('title', 'Unknown')
            uploader_name = doc.get('metadata', {}).get('uploader_name', 'Unknown')
            uploader_id = doc.get('user_id', 'unknown')
            
            print(f"\n[{doc_num}/{len(documents)}] Processing: {title}")
            print(f"  Subject: {subject}, ID: {content_id[:16]}...")
            
            # Get sample content for this subject
            content = SAMPLE_CONTENT.get(subject, SAMPLE_CONTENT['Chemistry'])
            
            # Chunk the content
            chunks = chunk_text(content)
            print(f"  Created {len(chunks)} chunks")
            
            # Generate embeddings and store in Pinecone
            vectors_to_upsert = []
            
            for i, chunk_text in enumerate(chunks):
                # Generate embedding
                response = await openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=chunk_text
                )
                
                embedding = response.data[0].embedding
                
                # Create vector with metadata
                vector = {
                    "id": f"{content_id}-chunk-{i}",
                    "values": embedding,
                    "metadata": {
                        "content_id": content_id,
                        "chunk_id": f"{content_id}-chunk-{i}",
                        "chunk_index": i,
                        "text": chunk_text[:40000],  # Pinecone metadata limit
                        "token_count": len(chunk_text.split()),
                        "subject": subject,
                        "document_title": title,
                        "uploader_name": uploader_name,
                        "uploader_id": uploader_id,
                        "upload_date": doc.get('upload_date').isoformat() if hasattr(doc.get('upload_date'), 'isoformat') else str(doc.get('upload_date', ''))
                    }
                }
                
                vectors_to_upsert.append(vector)
            
            # Upsert to Pinecone in namespace
            if vectors_to_upsert:
                index.upsert(vectors=vectors_to_upsert, namespace=content_id)
                print(f"  ✓ Uploaded {len(vectors_to_upsert)} vectors to Pinecone namespace: {content_id[:16]}...")
                total_vectors += len(vectors_to_upsert)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("VECTORIZATION COMPLETE!")
        print("=" * 60)
        print(f"✓ Processed {len(documents)} documents")
        print(f"✓ Created {total_vectors} vectors in Pinecone")
        print(f"✓ Chat is now enabled for all documents!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mongo_client.close()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         Vectorize Seeded Documents Script               ║
    ║                                                          ║
    ║  This creates Pinecone vectors for test documents       ║
    ║  to enable chat functionality.                          ║
    ║                                                          ║
    ║  Requirements:                                           ║
    ║  - PINECONE_API_KEY environment variable                ║
    ║  - OPENAI_API_KEY environment variable                  ║
    ║  - Documents in MongoDB                                  ║
    ║                                                          ║
    ║  Time: ~5-10 minutes for 11 documents                   ║
    ║  Cost: ~$0.10 for embeddings                            ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    confirm = input("Continue with vectorization? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Cancelled.")
        exit(0)
    
    asyncio.run(vectorize_documents())
    print("\n✅ Done! Chat is now enabled for all documents.")
    print("   Test it at: http://localhost:3003")

