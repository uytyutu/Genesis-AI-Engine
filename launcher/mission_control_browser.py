"""Backward-compatible import — prefer mission_control_surface.open_mission_control."""

from launcher.mission_control_surface import open_mission_control

__all__ = ["open_mission_control"]
