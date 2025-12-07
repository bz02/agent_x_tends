"""
Conversation Graph using Langraph for managing conversation flow
"""

import os
from typing import Dict, List, Any, Optional
try:
    from typing import TypedDict
except ImportError:
    # Python < 3.8
    from typing_extensions import TypedDict
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    ToolNode = None

from analyze_and_support import GrokClient


class ConversationState(TypedDict):
    """State for conversation graph"""
    user_id: str
    username: str
    user_message: str
    conversation_history: List[Dict[str, Any]]
    memory: Dict[str, Any]
    rag_context: List[Dict[str, Any]]
    response: str
    reasoning: str
    updated_memory: Dict[str, Any]


class ConversationGraph:
    """Manages conversation flow using Langraph"""
    
    def __init__(self, grok_client: GrokClient, memory_manager, rag_manager):
        self.grok_client = grok_client
        self.memory_manager = memory_manager
        self.rag_manager = rag_manager
        self.graph = None
        
        if LANGGRAPH_AVAILABLE:
            self._build_graph()
    
    def _build_graph(self):
        """Build the Langraph conversation graph"""
        if not LANGGRAPH_AVAILABLE:
            return
        
        # Define the graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("analyze_context", self._analyze_context_node)
        workflow.add_node("retrieve_memory", self._retrieve_memory_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("update_memory", self._update_memory_node)
        
        # Define edges
        workflow.set_entry_point("analyze_context")
        workflow.add_edge("analyze_context", "retrieve_memory")
        workflow.add_edge("retrieve_memory", "generate_response")
        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)
        
        self.graph = workflow.compile()
    
    async def _analyze_context_node(self, state: ConversationState) -> ConversationState:
        """Analyze the conversation context"""
        # This node analyzes the user's message and context
        # For now, we'll use the existing state
        return state
    
    async def _retrieve_memory_node(self, state: ConversationState) -> ConversationState:
        """Retrieve relevant memories"""
        # Search memories for relevant information
        if state.get("user_message"):
            memories = self.memory_manager.search_memories(
                user_id=state["user_id"],
                query=state["user_message"],
                limit=5
            )
            state["memory"]["relevant_memories"] = memories
        
        return state
    
    async def _generate_response_node(self, state: ConversationState) -> ConversationState:
        """Generate response using Grok with context"""
        # Build context for Grok
        context_parts = []
        
        # Add RAG context
        if state.get("rag_context"):
            context_parts.append("Support resources:")
            for ctx in state["rag_context"]:
                context_parts.append(f"- {ctx.get('text', '')}")
        
        # Add relevant memories
        if state.get("memory", {}).get("relevant_memories"):
            context_parts.append("\nRelevant past conversations:")
            for mem in state["memory"]["relevant_memories"][:3]:
                context_parts.append(f"- {mem.get('text', '')[:100]}")
        
        # Add conversation history
        if state.get("conversation_history"):
            context_parts.append("\nRecent conversation:")
            for msg in state["conversation_history"][-3:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")[:100]
                context_parts.append(f"{role}: {content}")
        
        context = "\n".join(context_parts)
        
        # Build prompt for Grok
        prompt = f"""You are a compassionate AI therapist calling someone who agreed to talk with you. 
They may be going through a difficult time and need support to feel better and calm down.

Context about this conversation:
{context}

User's message: {state.get('user_message', '')}

Your goals:
1. Help them feel heard and understood
2. Help them calm down and feel better ("chill up")
3. Provide emotional support and validation
4. Guide them toward feeling more positive and relaxed

Guidelines:
- Be warm, empathetic, and genuine - you're here to help them feel better
- Listen actively and validate their feelings - acknowledge what they're going through
- Help them calm down - use calming language, breathing suggestions, or grounding techniques when appropriate
- Be encouraging and positive - help shift their perspective toward hope
- Keep responses conversational and natural for voice (2-3 sentences max)
- Don't rush - allow space for them to express themselves
- If they mention specific concerns, address them with care and offer practical support
- Use the support resources provided in context when appropriate
- Remember: Your goal is to help them feel better, calmer, and more supported

Generate a supportive, calming response that helps them feel better. Focus on making them feel heard, validated, and more at ease."""

        # Generate response using Grok
        try:
            response = self.grok_client.analyze_sentiment(
                post_text=state.get("user_message", ""),
                username=state.get("username", "")
            )
            
            # Use Grok's chat completion for response generation
            import requests
            grok_response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.grok_client.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a compassionate, supportive voice assistant providing emotional support."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if grok_response.status_code == 200:
                result = grok_response.json()
                state["response"] = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                state["response"] = "I'm here to listen and support you. How are you feeling right now?"
            
        except Exception as e:
            print(f"Error generating response: {e}")
            state["response"] = "I'm here to listen and support you. How are you feeling right now?"
        
        state["reasoning"] = "Generated response using context-aware Grok API"
        return state
    
    async def _update_memory_node(self, state: ConversationState) -> ConversationState:
        """Update memory with new information"""
        # Save important information to memory
        if state.get("user_message") and len(state["user_message"]) > 20:
            self.memory_manager.add_memory(
                user_id=state["user_id"],
                memory_text=f"User said: {state['user_message']}",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "context": "voice_call"
                }
            )
        
        state["updated_memory"] = self.memory_manager.get_user_memory(state["user_id"])
        return state
    
    async def generate_initial_greeting(
        self,
        user_id: str,
        username: str,
        context: Optional[Dict],
        memory: Dict,
        rag_context: List[Dict]
    ) -> str:
        """Generate initial greeting for a call"""
        # Build personalized greeting
        original_post = context.get("original_post", "") if context else ""
        concerns = context.get("sentiment_analysis", {}).get("concerns", []) if context else []
        
        concerns_str = ", ".join(concerns) if concerns else "general concerns"
        
        prompt = f"""You are calling @{username} to offer support as an AI therapist. They posted on social media: "{original_post[:200]}"

They may be dealing with: {concerns_str}

They agreed to talk with you, so they're open to receiving help.

Generate a warm, natural, spoken greeting (2-3 sentences) that:
- Introduces yourself as an AI therapist who's here to help
- Acknowledges you saw their post and understand they're going through something
- Reassures them that you're here to listen and help them feel better
- Sets a calming, supportive tone for the conversation
- Feels genuine and not scripted
- Is appropriate for a voice call

Keep it conversational, warm, and focused on making them feel comfortable and supported."""

        try:
            import requests
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.grok_client.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-4-0709",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a compassionate person making a supportive phone call."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                return f"Hi {username}, I saw your post and wanted to reach out. I'm here to listen if you'd like to talk."
        except Exception as e:
            print(f"Error generating greeting: {e}")
            return f"Hi {username}, I saw your post and wanted to reach out. I'm here to listen if you'd like to talk."
    
    async def generate_response(
        self,
        user_id: str,
        username: str,
        user_message: str,
        conversation_history: List[Dict],
        memory: Dict,
        rag_context: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a response using the conversation graph"""
        if self.graph and LANGGRAPH_AVAILABLE:
            # Use Langraph
            state: ConversationState = {
                "user_id": user_id,
                "username": username,
                "user_message": user_message,
                "conversation_history": conversation_history,
                "memory": memory,
                "rag_context": rag_context,
                "response": "",
                "reasoning": "",
                "updated_memory": {}
            }
            
            result = await self.graph.ainvoke(state)
            return {
                "content": result.get("response", ""),
                "reasoning": result.get("reasoning", ""),
                "updated_memory": result.get("updated_memory", {})
            }
        else:
            # Fallback: direct Grok call
            return await self._generate_response_node({
                "user_id": user_id,
                "username": username,
                "user_message": user_message,
                "conversation_history": conversation_history,
                "memory": memory,
                "rag_context": rag_context,
                "response": "",
                "reasoning": "",
                "updated_memory": {}
            })

