"""Optional MQTT 5 publish adapter.

This adapter returns only a transport-level success. A deployment must add a
GXP ingestion-ack response-topic flow before using it to delete durable outbox
records; consequently it is intentionally not wired into EdgeAgent.flush yet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ..errors import TransportFailure


@dataclass
class MqttPublishAdapter:
    host: str
    port: int
    topic_prefix: str = "gxp/v1"
    tls: bool = True

    def publish_transport_only(self, envelope: dict[str, object]) -> None:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise TransportFailure("MQTT adapter requires the project mqtt extra.") from exc
        client = mqtt.Client(protocol=mqtt.MQTTv5)
        if self.tls:
            client.tls_set()
        try:
            client.connect(self.host, self.port)
            topic = f"{self.topic_prefix}/{envelope['tenant']}/{envelope['device']['id']}/events"
            result = client.publish(topic, json.dumps(envelope), qos=1)
            result.wait_for_publish()
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise TransportFailure(f"MQTT publish failed with result {result.rc}.")
        except OSError as exc:
            raise TransportFailure(f"MQTT publish failed: {exc}") from exc
        finally:
            client.disconnect()

