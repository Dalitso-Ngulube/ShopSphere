from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    body_text: str
    body_html: str | None = None


class EmailTransport(ABC):
    @abstractmethod
    def send_email(self, message: EmailMessage) -> None:
        """Send an email message through the configured transport."""


class ConsoleEmailTransport(EmailTransport):
    """Development/test adapter that writes email payloads to stdout."""

    def send_email(self, message: EmailMessage) -> None:
        print(
            f"[EMAIL:CONSOLE] to={message.recipient} subject={message.subject}\n"
            f"{message.body_text}"
        )
