class ExampleWarnPlugin:
    name = "example-warn"
    version = "1.0.0"
    min_sop_version = "0.2.0"

    def evaluate(self, action: dict, context: dict) -> dict | None:
        gate = str(context.get("gate", "")).strip()
        if gate == "advisory->summary":
            return {
                "decision": "WARN",
                "reason": "summary gate observed by example plugin",
                "metadata": {"gate": gate, "trace_id": context.get("trace_id")},
            }
        return None


plugin = ExampleWarnPlugin()
