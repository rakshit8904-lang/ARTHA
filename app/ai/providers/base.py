"""Provider-neutral chat interface for Artha AI."""

from abc import ABC, abstractmethod


class ProviderError(RuntimeError):
    """Safe, user-facing provider failure; never contains request content."""


class ChatProvider(ABC):
    name = "base"

    @abstractmethod
    def complete(self, messages, *, system_prompt, temperature=0.2):
        """Return assistant text for a validated sequence of messages."""
