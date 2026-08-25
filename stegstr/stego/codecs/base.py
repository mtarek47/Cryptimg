"""
Steganographic Codec Abstract Base Class
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
from PIL import Image


class StegoCodecError(Exception):
    pass


class BaseStegoCodec(ABC):
    @property
    @abstractmethod
    def mode_id(self) -> int:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def encode(self, image: Image.Image, payload: bytes, parameters: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Embed binary payload into PIL Image.
        Returns new PIL Image carrying the steganographic data.
        """
        pass

    @abstractmethod
    def decode(self, image: Image.Image, parameters: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Extract binary payload from PIL Image.
        Returns extracted raw payload bytes.
        """
        pass

    @abstractmethod
    def estimate_capacity(self, image: Image.Image, parameters: Optional[Dict[str, Any]] = None) -> int:
        """
        Estimate available payload capacity (in bytes) for given image.
        """
        pass
