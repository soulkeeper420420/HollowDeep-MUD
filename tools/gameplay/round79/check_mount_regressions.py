"""Run the prior native rest/travel/HUD socket test against the mount build."""
from pathlib import Path

original = Path(__file__).with_name("check_breath_rest_socket.py")
text = original.read_text().replace("hd-army-game-round79rest-", "hd-army-game-round79mount-")
exec(compile(text, str(original), "exec"), {"__file__": str(original), "__name__": "__main__"})
