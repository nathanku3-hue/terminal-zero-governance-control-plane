class ReferenceIamSiemConnectorPlugin:
    """Phase E D3 reference plugin: IAM/SIEM connector (v2)."""

    name = "reference-iam-siem-connector"
    version = "2.0.0"
    min_sop_version = "0.2.0"
    api_version = "2.0"
    kind = "iam_siem_connector"
    capabilities = ["iam_siem.emit_event"]

    def evaluate(self, action: dict, context: dict) -> dict | None:
        gate = str(context.get("gate", "")).strip()
        if gate == "reference-demo":
            return {
                "decision": "WARN",
                "reason": "reference IAM/SIEM connector demo event emission",
                "metadata": {
                    "plugin_kind": self.kind,
                    "gate": gate,
                    "trace_id": context.get("trace_id"),
                },
            }
        return None


plugin = ReferenceIamSiemConnectorPlugin()
