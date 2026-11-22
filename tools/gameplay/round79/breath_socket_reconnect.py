"""Pure socket-banner validation for Round79K saved-room reconnect.

The native MUD correctly loads the character's durable saved room after
logout. The older generic login helper assumes the original seed room,
which is not valid after a player has traveled.
"""
import re

_ANSI=re.compile(r"\x1b\[[0-9;]*m")

def require_saved_login_banner(banner, expected_room, expected_breath):
    if not isinstance(banner, (bytes, bytearray)):
        raise TypeError("Expected raw native MUD login socket bytes")
    if not expected_room or not isinstance(expected_breath, int) or not 0<=expected_breath<=100:
        raise ValueError("Invalid expected native room or Breath")
    rendered=_ANSI.sub("",bytes(banner).decode("latin-1","replace"))
    if expected_room not in rendered:
        raise AssertionError(
            "Reconnected character is not in saved room: "
            +repr(expected_room)+"; banner tail="+repr(rendered[-450:]))
    marker="Breath %d/100"%expected_breath
    if marker not in rendered:
        raise AssertionError(
            "Reconnected character Breath mismatch: "
            +marker+"; banner tail="+repr(rendered[-450:]))
    return rendered
