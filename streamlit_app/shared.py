from types import SimpleNamespace

bg_data = SimpleNamespace(
    connected=False,
    last_check=None,
    current_alert=None,
    status="⏳ Waiting for connection..."
)