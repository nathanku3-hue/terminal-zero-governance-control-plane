class ReferencePolicyEvaluatorPlugin:
    """Phase E D3 reference plugin: policy evaluator (v2)."""

    name = "reference-policy-evaluator"
    version = "2.0.0"
    min_sop_version = "0.2.0"
    api_version = "2.0"
    kind = "policy_evaluator"
    capabilities = ["policy.read_context", "policy.emit_decision"]

    def evaluate(self, action: dict, context: dict) -> dict | None:
        gate = str(context.get("gate", "")).strip()
        if gate == "reference-demo":
            return {
                "decision": "WARN",
                "reason": "reference policy evaluator demo decision",
                "metadata": {
                    "plugin_kind": self.kind,
                    "actor": action.get("actor"),
                    "trace_id": context.get("trace_id"),
                },
            }
        return None


plugin = ReferencePolicyEvaluatorPlugin()
