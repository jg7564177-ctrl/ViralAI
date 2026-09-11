from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class CreditMovement:
    type: str
    amount: int
    reason: str
    created_at: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "type": self.type,
            "amount": self.amount,
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass
class Account:
    user_id: str
    name: str
    role: str
    credits: int = 0
    free_credits: int = 0
    is_admin: bool = False
    is_active: bool = True
    metadata: Dict[str, object] = field(default_factory=dict)
    history: List[CreditMovement] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "credits": self.credits,
            "free_credits": self.free_credits,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "history": [movement.to_dict() for movement in self.history],
        }

    def to_safe_dict(self) -> Dict[str, object]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": "USER" if not self.is_admin else "ADMIN",
            "credits": self.credits,
            "free_credits": self.free_credits,
            "credits_available": self.credits + self.free_credits,
            "credits_consumed": 0,
            "is_active": self.is_active,
            "history": [movement.to_dict() for movement in self.history],
            "payment_history": [],
            "purchase_history": [],
            "account_status": "active" if self.credits + self.free_credits > 0 else "credit_blocked",
            "purchase_window_visible": (self.credits + self.free_credits) == 0,
        }


class AccountService:
    def __init__(self):
        self.accounts: Dict[str, Account] = {
            "admin": Account(
                user_id="admin",
                name="Admin",
                role="ADMIN",
                credits=0,
                free_credits=0,
                is_admin=True,
                metadata={"billing": "none", "plan": "admin"},
            ),
            "demo": Account(
                user_id="demo",
                name="Nouveau utilisateur",
                role="USER",
                credits=0,
                free_credits=5,
                is_admin=False,
                metadata={"billing": "free-tier", "plan": "starter"},
            ),
        }
        self.pack_catalog: Dict[str, Dict[str, object]] = {
            "starter": {
                "id": "starter",
                "name": "Starter",
                "credits": 10,
                "normal_price": 10.0,
                "promo_price": 5.0,
                "discount_percent": 50,
                "active": True,
            }
        }
        self.payment_history: List[Dict[str, object]] = []
        self._payment_transactions: set[str] = set()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _record_movement(self, account: Account, movement_type: str, amount: int, reason: str) -> None:
        account.history.append(
            CreditMovement(
                type=movement_type,
                amount=amount,
                reason=reason,
                created_at=self._now_iso(),
            )
        )

    def list_accounts(self, requester_id: str | None = None, as_admin: bool = False) -> List[Dict[str, object]]:
        if as_admin:
            return [account.to_dict() for account in self.accounts.values()]
        if requester_id:
            account = self.accounts.get(requester_id)
            if account is None:
                return []
            return [account.to_safe_dict()]
        return []

    def get_account(self, user_id: str) -> Account | None:
        return self.accounts.get(user_id)

    def get_admin_account(self) -> Dict[str, object]:
        return self.accounts["admin"].to_dict()

    def create_user(self, user_id: str, name: str, role: str = "USER") -> Account:
        normalized = role.upper()
        account = Account(
            user_id=user_id,
            name=name,
            role=normalized,
            credits=0,
            free_credits=5 if normalized == "USER" else 0,
            is_admin=normalized == "ADMIN",
            metadata={"billing": "none" if normalized == "ADMIN" else "free-tier"},
        )
        if normalized == "USER":
            self._record_movement(account, "credit", 5, "initial_free_credits")
        self.accounts[user_id] = account
        return account

    def is_admin(self, user_id: str) -> bool:
        account = self.accounts.get(user_id)
        return bool(account and account.is_admin)

    def get_balance(self, user_id: str) -> int:
        account = self.accounts.get(user_id)
        if account is None:
            return 0
        return account.credits + account.free_credits

    def get_history(self, user_id: str) -> List[Dict[str, object]]:
        account = self.accounts.get(user_id)
        if account is None:
            return []
        return [movement.to_dict() for movement in account.history]

    def get_payment_history(self, user_id: str) -> List[Dict[str, object]]:
        return [record.copy() for record in self.payment_history if record.get("user_id") == user_id]

    def get_purchase_history(self, user_id: str) -> List[Dict[str, object]]:
        return self.get_payment_history(user_id)

    def get_account_summary(self, user_id: str) -> Dict[str, object]:
        account = self.accounts.get(user_id)
        if account is None:
            return {
                "user_id": user_id,
                "credits_available": 0,
                "credits_consumed": 0,
                "credit_history": [],
                "payment_history": [],
                "purchase_history": [],
                "account_status": "unknown",
                "purchase_window_visible": True,
            }

        credit_history = self.get_history(user_id)
        payment_history = self.get_payment_history(user_id)
        consumed = 0
        for movement in account.history:
            if movement.type == "debit":
                consumed += abs(int(movement.amount))

        balance = self.get_balance(user_id)
        summary = {
            "user_id": user_id,
            "credits_available": balance,
            "credits_consumed": consumed,
            "credit_history": credit_history,
            "payment_history": payment_history,
            "purchase_history": payment_history,
            "account_status": "active" if balance > 0 else "credit_blocked",
            "purchase_window_visible": balance == 0,
            "status_message": "Tes crédits sont épuisés." if balance == 0 else "Compte actif.",
        }
        return summary

    def can_generate(self, user_id: str) -> bool:
        account = self.accounts.get(user_id)
        if account is None:
            return False
        if account.is_admin:
            return True
        return account.free_credits > 0 or account.credits > 0

    def create_or_update_pack(
        self,
        pack_id: str,
        *,
        name: str,
        credits: int,
        normal_price: float,
        promo_price: float | None = None,
        active: bool = True,
        discount_percent: int | None = None,
    ) -> Dict[str, object]:
        normalized_id = (pack_id or "starter").strip()
        if not normalized_id:
            raise ValueError("pack_id is required")

        if promo_price is None and isinstance(discount_percent, int) and discount_percent > 0 and normal_price > 0:
            promo_price = round(normal_price * (100 - discount_percent) / 100, 2)

        if promo_price is None:
            promo_price = normal_price

        computed_discount = 0
        if normal_price > 0 and promo_price < normal_price:
            computed_discount = int(round((1 - (promo_price / normal_price)) * 100))
        if discount_percent is not None:
            computed_discount = int(discount_percent)

        pack = {
            "id": normalized_id,
            "name": name,
            "credits": int(credits),
            "normal_price": float(normal_price),
            "promo_price": float(promo_price),
            "discount_percent": computed_discount,
            "active": bool(active),
        }
        self.pack_catalog[normalized_id] = pack
        return pack

    def get_pack(self, pack_id: str) -> Dict[str, object] | None:
        return self.pack_catalog.get((pack_id or "").strip())

    def list_packs(self, public_only: bool = True) -> List[Dict[str, object]]:
        packs = list(self.pack_catalog.values())
        if public_only:
            return [pack.copy() for pack in packs if bool(pack.get("active"))]
        return [pack.copy() for pack in packs]

    def get_pack_price(self, pack_id: str, client_price: float | None = None) -> float:
        pack = self.pack_catalog.get((pack_id or "").strip())
        if pack is None:
            return 0.0
        if pack.get("active"):
            promo_price = pack.get("promo_price")
            if promo_price is not None:
                return float(promo_price)
        return float(pack.get("normal_price") or 0.0)

    def add_credits(self, user_id: str, amount: int, reason: str = "manual_adjustment", actor_id: str | None = None) -> int:
        if amount <= 0:
            return self.get_balance(user_id)
        account = self.accounts.get(user_id)
        if account is None:
            return 0
        account.credits += amount
        self._record_movement(account, "credit", amount, reason)
        return account.credits

    def remove_credits(self, user_id: str, amount: int, reason: str = "manual_adjustment", actor_id: str | None = None) -> int:
        if amount <= 0:
            return self.get_balance(user_id)
        account = self.accounts.get(user_id)
        if account is None:
            return 0
        remaining = amount
        if account.credits >= remaining:
            account.credits -= remaining
            self._record_movement(account, "debit", -remaining, reason)
            return account.credits
        if account.free_credits >= remaining:
            account.free_credits -= remaining
            self._record_movement(account, "debit", -remaining, reason)
            return account.credits
        if account.credits > 0:
            used_from_paid = min(account.credits, remaining)
            account.credits -= used_from_paid
            remaining -= used_from_paid
            self._record_movement(account, "debit", -used_from_paid, reason)
        if account.free_credits > 0 and remaining > 0:
            used_from_free = min(account.free_credits, remaining)
            account.free_credits -= used_from_free
            self._record_movement(account, "debit", -used_from_free, reason)
        return account.credits + account.free_credits

    def consume_credit_for_generation(self, user_id: str, amount: int = 1, reason: str = "video_generation") -> bool:
        account = self.accounts.get(user_id)
        if account is None:
            return False
        if account.is_admin:
            return True
        if self.get_balance(user_id) < amount:
            return False
        self.remove_credits(user_id, amount, reason=reason)
        return True

    def consume_credit(self, user_id: str, amount: int = 1, reason: str = "video_generation") -> bool:
        return self.consume_credit_for_generation(user_id, amount=amount, reason=reason)

    def refund_credit_after_failure(self, user_id: str, amount: int = 1, reason: str = "generation_failed") -> bool:
        account = self.accounts.get(user_id)
        if account is None:
            return False
        if account.is_admin:
            return True
        self.add_credits(user_id, amount, reason=reason)
        return True

    def record_payment(
        self,
        user_id: str,
        *,
        transaction_id: str,
        pack_id: str,
        amount: float,
        status: str,
        credits: int,
        currency: str = "USD",
    ) -> bool:
        account = self.accounts.get(user_id)
        if account is None:
            return False

        normalized_tx = str(transaction_id or "").strip()
        if not normalized_tx:
            normalized_tx = f"{user_id}-{len(self.payment_history) + 1}"
        if normalized_tx in self._payment_transactions:
            return False

        normalized_status = str(status or "PENDING").upper()
        if normalized_status in {"SUCCESS", "SUCCEEDED", "PAID", "COMPLETED"}:
            normalized_status = "SUCCESS"
        elif normalized_status in {"FAILED", "ERROR"}:
            normalized_status = "FAILED"
        elif normalized_status in {"REFUNDED", "REFUND"}:
            normalized_status = "REFUNDED"
        else:
            normalized_status = "PENDING"

        record = {
            "user_id": user_id,
            "transaction_id": normalized_tx,
            "pack_id": pack_id,
            "amount": float(amount),
            "currency": currency,
            "status": normalized_status,
            "credits_awarded": int(credits),
            "created_at": self._now_iso(),
        }
        self.payment_history.append(record)
        self._payment_transactions.add(normalized_tx)

        if normalized_status == "SUCCESS":
            self.add_credits(user_id, int(credits), reason=f"payment:{pack_id}")
        return True

    def require_admin(self, user_id: str) -> bool:
        return self.is_admin(user_id)

    def admin_summary(self) -> Dict[str, object]:
        users = []
        for account in self.accounts.values():
            users.append({
                "user_id": account.user_id,
                "name": account.name,
                "role": account.role,
                "credits": account.credits,
                "free_credits": account.free_credits,
                "is_admin": account.is_admin,
            })
        return {
            "users": users,
            "packs": self.list_packs(public_only=False),
            "payments": self.payment_history,
            "revenue": round(sum(float(entry.get("amount", 0)) for entry in self.payment_history if entry.get("status") == "SUCCESS"), 2),
        }
