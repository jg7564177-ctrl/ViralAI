from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


class ChatConversationService:
    def __init__(self):
        self.conversations: Dict[str, Dict[str, Any]] = {}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def create_conversation(self, user_id: str, title: str | None = None) -> Dict[str, Any]:
        conversation_id = f"chat-{uuid.uuid4().hex[:10]}"
        now = self._utc_now()
        conversation = {
            "id": conversation_id,
            "user_id": user_id,
            "title": (title or "Nouvelle conversation").strip() or "Nouvelle conversation",
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "project_id": None,
        }
        self.conversations[conversation_id] = conversation
        return self.get_conversation(conversation_id, user_id)

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        return [
            self._serialize(conversation)
            for conversation in self.conversations.values()
            if conversation.get("user_id") == user_id
        ]

    def get_conversation(self, conversation_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            return None
        if user_id is not None and conversation.get("user_id") != user_id:
            return None
        return self._serialize(conversation)

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.get("user_id") != user_id:
            return False
        del self.conversations[conversation_id]
        return True

    def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        timestamp: str | None = None,
    ) -> Dict[str, Any] | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.get("user_id") != user_id:
            return None

        normalized_role = (role or "user").strip().lower()
        if normalized_role not in {"user", "assistant"}:
            normalized_role = "user"

        normalized_content = (content or "").strip()
        if not normalized_content:
            raise ValueError("MESSAGE_EMPTY")

        message = {
            "role": normalized_role,
            "content": normalized_content,
            "timestamp": timestamp or self._utc_now(),
        }
        conversation["messages"].append(message)
        conversation["updated_at"] = self._utc_now()
        if normalized_role == "user" and not conversation.get("title"):
            conversation["title"] = self._title_from_message(normalized_content)
        elif normalized_role == "user":
            conversation["title"] = self._title_from_message(normalized_content, current_title=conversation.get("title"))
        return message

    def get_context(self, conversation_id: str, user_id: str, limit: int = 8) -> List[Dict[str, Any]]:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.get("user_id") != user_id:
            return []
        messages = conversation.get("messages", [])
        return list(messages[-limit:])

    def attach_project(self, conversation_id: str, user_id: str, project_id: str | None) -> Dict[str, Any] | None:
        conversation = self.conversations.get(conversation_id)
        if conversation is None or conversation.get("user_id") != user_id:
            return None
        conversation["project_id"] = project_id
        conversation["updated_at"] = self._utc_now()
        return self._serialize(conversation)

    def _serialize(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": conversation["id"],
            "user_id": conversation["user_id"],
            "title": conversation.get("title") or "Nouvelle conversation",
            "messages": conversation.get("messages", []),
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at"),
            "project_id": conversation.get("project_id"),
        }

    def _title_from_message(self, message: str, current_title: str | None = None) -> str:
        compact = " ".join(message.split())
        if len(compact) <= 42:
            return compact if compact else (current_title or "Nouvelle conversation")
        return compact[:39].rstrip() + "..."
