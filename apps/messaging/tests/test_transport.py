import pytest
from django.core import mail
from django.test import override_settings

from apps.messaging.transports import (
    ConsoleEmailTransport,
    DjangoEmailTransport,
    EmailMessage,
    EmailTransport,
    Message,
    MessageTransport,
)


def make_email() -> EmailMessage:
    return EmailMessage(
        recipient="customer@example.com",
        subject="Welcome to ShopSphere",
        body_text="Welcome to ShopSphere.",
        body_html="<h1>Welcome to ShopSphere.</h1>",
    )


def test_email_message_implements_generic_message_contract():
    message = make_email()

    assert isinstance(message, Message)
    assert message.channel == "email"
    assert message.recipient == "customer@example.com"


def test_email_transport_implements_generic_transport_contract():
    transport = ConsoleEmailTransport()

    assert isinstance(transport, MessageTransport)
    assert isinstance(transport, EmailTransport)


def test_console_email_transport_sends_message(capsys):
    transport = ConsoleEmailTransport()

    transport.send(make_email())

    output = capsys.readouterr().out

    assert "[EMAIL:CONSOLE]" in output
    assert "customer@example.com" in output
    assert "Welcome to ShopSphere." in output
    assert "<h1>Welcome to ShopSphere.</h1>" in output


def test_email_transport_rejects_unsupported_message_type():
    class UnsupportedMessage(Message):
        @property
        def recipient(self) -> str:
            return "customer@example.com"

        @property
        def channel(self) -> str:
            return "unsupported"

    transport = ConsoleEmailTransport()

    with pytest.raises(TypeError, match="only supports EmailMessage"):
        transport.send(UnsupportedMessage())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_django_email_transport_sends_email():
    transport = DjangoEmailTransport()

    transport.send(make_email())

    assert len(mail.outbox) == 1

    sent_email = mail.outbox[0]

    assert sent_email.subject == "Welcome to ShopSphere"
    assert sent_email.to == ["customer@example.com"]
    assert sent_email.body == "Welcome to ShopSphere."

    assert ("<h1>Welcome to ShopSphere.</h1>", "text/html") in sent_email.alternatives


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_django_email_transport_sends_plain_text_without_html():
    transport = DjangoEmailTransport()

    transport.send(
        EmailMessage(
            recipient="customer@example.com",
            subject="Plain text email",
            body_text="This email has no HTML alternative.",
        )
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].body == "This email has no HTML alternative."
    assert mail.outbox[0].alternatives == []
