# Shadowed Module Fixture — Notes
The file `scripts/phase_gate.py` in this fixture raises `ImportError` intentionally.
It is NOT on `sys.path` and does NOT cause real import-time shadowing.
The Phase 1 negative gate is validated at the unit test level:
`TestShadowedModuleFixture` uses `mock.patch` on `importlib.util.find_spec`
to simulate a fake module origin. This is the intentional and documented approach.
Real `sys.path` shadowing is out of scope for Phase 1.
