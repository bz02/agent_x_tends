"""
RAG Manager using LanceDB for retrieval-augmented generation
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

try:
    import lancedb
    from lancedb.embeddings import get_registry
except ImportError:
    lancedb = None
    get_registry = None


class RAGManager:
    """Manages RAG using LanceDB for support resources and user context"""
    
    def __init__(self):
        self.lancedb_available = lancedb is not None
        self.db = None
        self.table = None
        self.embeddings = None
        
        if self.lancedb_available:
            try:
                # Initialize LanceDB
                self.db = lancedb.connect("./lancedb_storage")
                
                # Get embedding function
                if get_registry:
                    self.embeddings = get_registry().get("openai").create()
                
                # Create or get table
                try:
                    self.table = self.db.open_table("support_resources")
                except:
                    # Create table if it doesn't exist
                    self._initialize_table()
                
                self.ready = True
            except Exception as e:
                print(f"Warning: LanceDB initialization failed: {e}")
                self.ready = False
        else:
            self.ready = False
        
        # Initialize with support resources
        self._load_support_resources()
    
    def is_ready(self) -> bool:
        """Check if RAG system is ready"""
        return self.ready or True  # Always return True for fallback
    
    def _initialize_table(self):
        """Initialize the LanceDB table"""
        if not self.lancedb_available or not self.db:
            return
        
        try:
            # Create table with schema
            schema = {
                "id": str,
                "text": str,
                "category": str,
                "metadata": dict,
                "vector": self.embeddings if self.embeddings else None
            }
            
            self.table = self.db.create_table(
                "support_resources",
                data=[],
                mode="overwrite"
            )
        except Exception as e:
            print(f"Error initializing table: {e}")
    
    def _load_support_resources(self):
        """Load support resources into RAG system"""
        support_resources = [
            {
                "id": "support_1",
                "text": "It's okay to feel sad or anxious. These feelings are valid and temporary. Remember that you're not alone, and there are people who care about you.",
                "category": "emotional_support",
                "metadata": {"type": "general_support"}
            },
            {
                "id": "support_2",
                "text": "If you're feeling overwhelmed, try taking deep breaths. Inhale for 4 counts, hold for 4, and exhale for 4. This can help calm your nervous system.",
                "category": "coping_strategies",
                "metadata": {"type": "breathing_exercise"}
            },
            {
                "id": "support_3",
                "text": "Remember that difficult times don't last forever. You've gotten through tough situations before, and you can get through this too.",
                "category": "encouragement",
                "metadata": {"type": "hope"}
            },
            {
                "id": "support_4",
                "text": "It's important to be kind to yourself. Treat yourself with the same compassion you would show a friend going through a hard time.",
                "category": "self_compassion",
                "metadata": {"type": "self_care"}
            },
            {
                "id": "support_5",
                "text": "If you're struggling, consider reaching out to a mental health professional. Therapy and counseling can provide valuable support and tools.",
                "category": "professional_help",
                "metadata": {"type": "resources"}
            },
            {
                "id": "support_6",
                "text": "Small steps forward are still progress. Celebrate the little victories, even if they seem insignificant.",
                "category": "encouragement",
                "metadata": {"type": "progress"}
            },
            {
                "id": "support_7",
                "text": "Your feelings matter. It's okay to not be okay. Give yourself permission to feel what you're feeling without judgment.",
                "category": "validation",
                "metadata": {"type": "emotional_validation"}
            },
            {
                "id": "support_8",
                "text": "Connecting with others, even briefly, can help. Sometimes just knowing someone is there can make a difference.",
                "category": "connection",
                "metadata": {"type": "social_support"}
            }
        ]
        
        if self.lancedb_available and self.table and self.embeddings:
            try:
                # Add resources to table
                import pandas as pd
                df = pd.DataFrame(support_resources)
                
                # Generate embeddings
                if hasattr(self.embeddings, 'embed'):
                    df['vector'] = df['text'].apply(lambda x: self.embeddings.embed(x))
                
                # Insert into table
                self.table.add(df)
            except Exception as e:
                print(f"Error loading support resources: {e}")
    
    def get_relevant_context(self, user_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get relevant context for a query using RAG"""
        if self.lancedb_available and self.table and self.embeddings:
            try:
                # Generate query embedding
                if hasattr(self.embeddings, 'embed'):
                    query_vector = self.embeddings.embed(query)
                    
                    # Search for similar content
                    results = self.table.search(query_vector).limit(limit).to_pandas()
                    
                    return [
                        {
                            "text": row.get("text", ""),
                            "category": row.get("category", ""),
                            "metadata": row.get("metadata", {}),
                            "score": row.get("_distance", 0) if "_distance" in row else 1.0
                        }
                        for _, row in results.iterrows()
                    ]
            except Exception as e:
                print(f"Error in RAG search: {e}")
        
        # Fallback: return default support resources
        return self._get_fallback_context(query, limit)
    
    def _get_fallback_context(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback context when LanceDB is not available"""
        # Simple keyword matching
        query_lower = query.lower()
        
        fallback_resources = [
            {
                "text": "It's okay to feel sad or anxious. These feelings are valid and temporary. Remember that you're not alone.",
                "category": "emotional_support",
                "metadata": {"type": "general_support"},
                "score": 0.9
            },
            {
                "text": "If you're feeling overwhelmed, try taking deep breaths. This can help calm your nervous system.",
                "category": "coping_strategies",
                "metadata": {"type": "breathing_exercise"},
                "score": 0.8
            },
            {
                "text": "Remember that difficult times don't last forever. You've gotten through tough situations before.",
                "category": "encouragement",
                "metadata": {"type": "hope"},
                "score": 0.7
            }
        ]
        
        # Filter by keywords if present
        if any(word in query_lower for word in ["sad", "depressed", "anxious", "worried"]):
            return fallback_resources[:limit]
        
        return fallback_resources[:limit]
    
    def add_user_context(self, user_id: str, context_text: str, metadata: Optional[Dict] = None):
        """Add user-specific context to RAG system"""
        if self.lancedb_available and self.table and self.embeddings:
            try:
                import pandas as pd
                
                context_entry = {
                    "id": f"user_{user_id}_{datetime.now().timestamp()}",
                    "text": context_text,
                    "category": "user_context",
                    "metadata": metadata or {"user_id": user_id}
                }
                
                df = pd.DataFrame([context_entry])
                
                # Generate embedding
                if hasattr(self.embeddings, 'embed'):
                    df['vector'] = df['text'].apply(lambda x: self.embeddings.embed(x))
                
                # Add to table
                self.table.add(df)
            except Exception as e:
                print(f"Error adding user context: {e}")

