"""NotificationPlugin interface — deliver messages through external channels."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from plugin_sdk.base import PluginBase


class NotificationPlugin(PluginBase):
    """Sends notifications through an external channel (Slack, email, webhook, etc.)."""

    @abstractmethod
    async def notify(self, message: str, channel: str, **kwargs: Any) -> None:
        """Send ``message`` to ``channel``.

        ``channel`` semantics are implementation-defined (Slack channel name,
        email address, webhook URL, etc.).  Extra ``kwargs`` pass
        implementation-specific options such as priority or attachments.
        """
        ...
