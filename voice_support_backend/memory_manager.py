"""
Memory Manager using Mem0 for long-term memory storage
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

try:
    from mem0 import Memory
except ImportError:
    # Fallback if Mem0 is not available
    Memory = None


class MemoryManager:
    """Manages long-term memory for users using Mem0"""
    
    def __init__(self):
        self.mem0_available = Memory is not None
        if self.mem0_available:
            try:
                # Initialize Mem0 with vector store
                self.memory = Memory(
                    vector_store={
                        "provider": "chroma",
                        "config": {
                            "collection_name": "user_memories",
                            "path": "./mem0_storage"
                        }
                    }
                )
                self.ready = True
            except Exception as e:
                print(f"Warning: Mem0 initialization failed: {e}")
                self.memory = None
                self.ready = False
        else:
            self.memory = None
            self.ready = False
        
        # Fallback: file-based storage
        self.storage_path = Path("./conversation_storage")
        self.storage_path.mkdir(exist_ok=True)
    
    def is_ready(self) -> bool:
        """Check if memory system is ready"""
        return self.ready or True  # Always return True for fallback
    
    def get_user_memory(self, user_id: str) -> Dict[str, Any]:
        """Get all memories for a user"""
        if self.mem0_available and self.memory:
            try:
                memories = self.memory.get_all(user_id=user_id)
                return {
                    "memories": memories,
                    "count": len(memories) if memories else 0
                }
            except Exception as e:
                print(f"Error getting memories from Mem0: {e}")
        
        # Fallback: read from file
        return self._get_file_memory(user_id)
    
    def add_memory(self, user_id: str, memory_text: str, metadata: Optional[Dict] = None):
        """Add a memory for a user"""
        if self.mem0_available and self.memory:
            try:
                self.memory.add(
                    user_id=user_id,
                    memory=memory_text,
                    metadata=metadata or {}
                )
                return
            except Exception as e:
                print(f"Error adding memory to Mem0: {e}")
        
        # Fallback: save to file
        self._save_file_memory(user_id, memory_text, metadata)
    
    def add_message(self, user_id: str, role: str, content: str):
        """Add a conversation message (also creates memory)"""
        timestamp = datetime.now().isoformat()
        
        # Save message to conversation history
        self._save_message(user_id, role, content, timestamp)
        
        # Extract important information for memory
        if role == "user" and len(content) > 20:
            # Only save substantial user messages as memories
            self.add_memory(
                user_id=user_id,
                memory_text=f"User said: {content}",
                metadata={"role": role, "timestamp": timestamp}
            )
    
    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search memories for a user"""
        if self.mem0_available and self.memory:
            try:
                results = self.memory.search(
                    user_id=user_id,
                    query=query,
                    limit=limit
                )
                return results if results else []
            except Exception as e:
                print(f"Error searching memories: {e}")
        
        # Fallback: simple text search
        return self._search_file_memories(user_id, query, limit)
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a user"""
        history_file = self.storage_path / f"{user_id}_history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
                conversations = data.get("conversations", [])
                return conversations[-limit:] if limit else conversations
        except Exception as e:
            print(f"Error reading conversation history: {e}")
            return []
    
    def _get_file_memory(self, user_id: str) -> Dict[str, Any]:
        """Fallback: get memory from file"""
        memory_file = self.storage_path / f"{user_id}_memory.json"
        
        if not memory_file.exists():
            return {"memories": [], "count": 0}
        
        try:
            with open(memory_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading file memory: {e}")
            return {"memories": [], "count": 0}
    
    def _save_file_memory(self, user_id: str, memory_text: str, metadata: Optional[Dict]):
        """Fallback: save memory to file"""
        memory_file = self.storage_path / f"{user_id}_memory.json"
        
        memory_data = self._get_file_memory(user_id)
        memory_entry = {
            "text": memory_text,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        memory_data["memories"].append(memory_entry)
        memory_data["count"] = len(memory_data["memories"])
        
        try:
            with open(memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
        except Exception as e:
            print(f"Error saving file memory: {e}")
    
    def _save_message(self, user_id: str, role: str, content: str, timestamp: str):
        """Save message to conversation history"""
        history_file = self.storage_path / f"{user_id}_history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"conversations": []}
        
        # Find or create current conversation
        if not data["conversations"] or data["conversations"][-1].get("ended"):
            data["conversations"].append({
                "started_at": timestamp,
                "messages": [],
                "ended": False
            })
        
        # Add message to current conversation
        current_conv = data["conversations"][-1]
        current_conv["messages"].append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
        
        try:
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving message: {e}")
    
    def _search_file_memories(self, user_id: str, query: str, limit: int) -> List[Dict]:
        """Fallback: search memories in file"""
        memory_data = self._get_file_memory(user_id)
        memories = memory_data.get("memories", [])
        
        # Simple text matching
        query_lower = query.lower()
        results = [
            mem for mem in memories
            if query_lower in mem.get("text", "").lower()
        ]
        
        return results[:limit]

