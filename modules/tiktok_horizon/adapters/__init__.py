"""External service adapters — swappable without touching Horizon core."""

from modules.tiktok_horizon.adapters.base import AdapterResult, ExternalAdapter
from modules.tiktok_horizon.adapters.tiktok_api import TikTokOfficialAdapter
from modules.tiktok_horizon.adapters.tts_api import TtsAdapter
from modules.tiktok_horizon.adapters.video_api import VideoGeneratorAdapter

__all__ = [
    "AdapterResult",
    "ExternalAdapter",
    "TikTokOfficialAdapter",
    "TtsAdapter",
    "VideoGeneratorAdapter",
]
