from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.core.mail import EmailMultiAlternatives


class Message(ABC):
    """Base contract for messages sent through the messaging system."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Return the message delivery channel."""


@dataclass(frozen=True)
class EmailMessage(Message):
    recipient: str
    subject: str
    body_text: str
    body_html: str | None = None

    @property
    def channel(self) -> str:
        return "email"


class MessageTransport(ABC):
    """Generic interface implemented by message delivery transports."""

    @abstractmethod
    def send(self, message: Message) -> None:
        """Deliver a message through the configured transport."""


class EmailTransport(MessageTransport, ABC):
    """Base contract for email-specific transport adapters."""

    def send(self, message: Message) -> None:
        if not isinstance(message, EmailMessage):
            raise TypeError("EmailTransport only supports EmailMessage instances.")

        self.send_email(message)

    @abstractmethod
    def send_email(self, message: EmailMessage) -> None:
        """Deliver an email message."""


class ConsoleEmailTransport(EmailTransport):
    """Development/test adapter that writes email payloads to stdout."""

    def send_email(self, message: EmailMessage) -> None:
        print(
            f"[EMAIL:CONSOLE] to={message.recipient} "
            f"subject={message.subject}\n{message.body_text}"
        )

        if message.body_html:
            print(f"[EMAIL:HTML]\n{message.body_html}")


class DjangoEmailTransport(EmailTransport):
    """Email adapter using Django's configured email backend."""

    def send_email(self, message: EmailMessage) -> None:
        email = EmailMultiAlternatives(
            subject=message.subject,
            body=message.body_text,
            to=[message.recipient],
        )

        if message.body_html:
            email.attach_alternative(message.body_html, "text/html")

        sent_count = email.send(fail_silently=False)

        if sent_count != 1:
            raise RuntimeError(f"Email delivery failed for recipient {message.recipient!r}.")
