class ReferenceDecisionStorePlugin:
    """Phase E D3 reference plugin: decision store connector (v2)."""

    name = "reference-decision-store"
    version = "2.0.0"
    min_sop_version = "0.2.0"
    api_version = "2.0"
    kind = "decision_store"
    capabilities = ["decision_store.read", "decision_store.write"]

    def evaluate(self, action: dict, context: dict) -> dict | None:
        gate = str(context.get("gate", "")).strip()
        if gate == "reference-demo":
            return {
                "decision": "ALLOW",
                "reason": "reference decision store connector demo decision",
                "metadata": {
                    "plugin_kind": self.kind,
                    "gate": gate,
                    "trace_id": context.get("trace_id"),
                },
            }
        return None


plugin = ReferenceDecisionStorePlugin()
