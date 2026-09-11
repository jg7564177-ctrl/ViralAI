from app import app
from services.account_service import AccountService


def test_user_account_summary_includes_credit_and_payment_data():
    service = AccountService()
    service.create_user("buyer", "Buyer")

    summary = service.get_account_summary("buyer")
    assert summary["credits_available"] == 5
    assert summary["credits_consumed"] == 0
    assert summary["account_status"] == "active"
    assert "payment_history" in summary
    assert "purchase_history" in summary
    assert "credit_history" in summary


def test_admin_can_manage_credit_packs_and_server_side_discount():
    service = AccountService()
    service.create_user("buyer", "Buyer")

    pack = service.create_or_update_pack(
        "starter",
        name="Starter",
        credits=10,
        normal_price=10,
        promo_price=5,
        active=True,
    )

    assert pack["credits"] == 10
    assert service.get_pack_price("starter") == 5
    assert service.get_pack_price("starter", client_price=999) == 5


def test_duplicate_payment_transaction_does_not_double_credit():
    service = AccountService()
    service.create_user("buyer", "Buyer")

    tx_id = "tx-123"
    first = service.record_payment(
        "buyer",
        transaction_id=tx_id,
        pack_id="starter",
        amount=10,
        status="SUCCESS",
        credits=10,
    )
    second = service.record_payment(
        "buyer",
        transaction_id=tx_id,
        pack_id="starter",
        amount=10,
        status="SUCCESS",
        credits=10,
    )

    assert first is True
    assert second is False
    assert service.get_balance("buyer") == 15
    assert len(service.get_payment_history("buyer")) == 1


def test_zero_credit_account_blocks_paid_actions_and_exposes_purchase_window():
    service = AccountService()
    service.create_user("empty-user", "Empty")
    service.remove_credits("empty-user", service.get_balance("empty-user"), reason="test_reset")

    assert service.get_balance("empty-user") == 0
    assert service.can_generate("empty-user") is False

    status = service.get_account_summary("empty-user")
    assert status["credits_available"] == 0
    assert status["purchase_window_visible"] is True
    assert status["account_status"] == "credit_blocked"


def test_payment_routes_report_not_configured_without_real_provider():
    client = app.test_client()
    response = client.post(
        "/api/payments/checkout",
        headers={"X-User-Id": "demo"},
        json={"pack_id": "starter"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "PAYMENT_NOT_CONFIGURED"
    assert "bientôt disponible" in payload["message"].lower()
    assert payload["credits_added"] == 0


def test_admin_packs_are_hidden_from_standard_users():
    client = app.test_client()
    response = client.get("/api/admin/packs", headers={"X-User-Id": "demo"})
    assert response.status_code == 403
