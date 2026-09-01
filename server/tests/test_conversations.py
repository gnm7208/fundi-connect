"""Tests for in-app messaging and conversation threads."""

from server.tests.conftest import auth_header_for


def test_start_conversation_and_send_message(app, client, sample_customer, sample_fundi):
    """Customer initiates chat with fundi and exchanges messages."""
    cust_headers = auth_header_for(app, sample_customer)
    fundi_headers = auth_header_for(app, sample_fundi)

    # 1. Start Conversation
    conv_res = client.post(
        "/api/v1/conversations",
        json={
            "fundi_id": sample_fundi.id,
            "initial_message": "Hello Mwangi, are you free tomorrow afternoon?",
        },
        headers=cust_headers,
    )
    assert conv_res.status_code == 200
    conv_id = conv_res.get_json()["conversation"]["id"]
    assert len(conv_res.get_json()["conversation"]["messages"]) == 1

    # 2. Fundi replies
    reply_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Yes Jane, 2:00 PM works for me."},
        headers=fundi_headers,
    )
    assert reply_res.status_code == 201

    # 3. Retrieve thread messages
    thread_res = client.get(f"/api/v1/conversations/{conv_id}", headers=cust_headers)
    assert thread_res.status_code == 200
    messages = thread_res.get_json()["conversation"]["messages"]
    assert len(messages) == 2
