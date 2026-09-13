"""
Top-Down Picture-in-Picture (PiP) Minimap Overlay.
Final Year Project - RSET
Collaborative Trajectory Planning & Multi-Agent Orchestration for CAVs

Renders a 2D overhead track minimap showing all vehicle locations, road segments,
and camera frustum, overlaid in the corner of the MetaDrive 3D viewport.
"""

import time
from typing import Any, Optional, Tuple
import numpy as np

from cav_demo.config import MinimapConfig


class MinimapRenderer:
    """
    Renders a live top-down minimap texture onto Panda3D viewport or companion display.
    """

    def __init__(self, config: Optional[MinimapConfig] = None):
        self.config = config or MinimapConfig()
        self.frame_count = 0
        self._texture = None
        self._onscreen_image = None
        self._initialized = False
        self._failed = False

    def init_overlay(self, env: Any):
        """Initialize Panda3D Texture and OnscreenImage node for PiP display."""
        if self._initialized or self._failed or not self.config.enabled:
            return

        engine = getattr(env, "engine", None)
        if engine is None:
            return

        try:
            from direct.gui.OnscreenImage import OnscreenImage
            from panda3d.core import Texture

            w, h = self.config.size
            self._texture = Texture("minimap_stream_tex")
            self._texture.setup2dTexture(w, h, Texture.T_unsigned_byte, Texture.F_rgb)
            
            # Initial blank buffer
            blank = np.zeros((h, w, 3), dtype=np.uint8)
            self._texture.setRamImage(blank.tobytes())

            # Pin to bottom-left corner of Panda3D aspect2d
            pos_x, pos_y = self.config.screen_pos
            self._onscreen_image = OnscreenImage(
                image=self._texture,
                pos=(pos_x, 0.0, pos_y),
                scale=(0.26, 1.0, 0.26)
            )
            self._initialized = True
        except Exception as e:
            # If Panda3D image overlay fails, fallback gracefully without crashing demo
            self._failed = True

    def update(self, env: Any, focused_agent_id: str):
        """
        Periodically extract top-down frame and refresh the minimap texture.
        """
        if not self.config.enabled or self._failed:
            return

        self.frame_count += 1
        if self.frame_count % self.config.update_interval_frames != 0:
            return

        if not self._initialized:
            self.init_overlay(env)

        # Generate topdown frame from MetaDrive
        try:
            # MetaDrive topdown render call
            frame = None
            if hasattr(env, "render"):
                try:
                    frame = env.render(
                        mode="topdown",
                        film_size=(self.config.size[0], self.config.size[1]),
                        screen_size=self.config.size,
                        scaling=self.config.scaling,
                        window=False
                    )
                except TypeError:
                    # Fallback for variant argument signatures
                    frame = env.render(mode="topdown")

            if frame is not None and self._texture is not None:
                # Ensure frame is RGB numpy array matching texture size
                if isinstance(frame, np.ndarray):
                    # Resize or convert if needed
                    h, w = self.config.size
                    if frame.shape[0] != h or frame.shape[1] != w:
                        from PIL import Image
                        img = Image.fromarray(frame)
                        img = img.resize((w, h))
                        frame = np.array(img)

                    # Update Panda3D Texture RAM
                    if frame.ndim == 3 and frame.shape[2] >= 3:
                        rgb_data = frame[:, :, :3].astype(np.uint8).tobytes()
                        self._texture.setRamImage(rgb_data)
        except Exception:
            # Gracefully handle frames if topdown mode is temporarily busy
            pass

    def destroy(self):
        """Clean up Panda3D texture node."""
        if self._onscreen_image is not None:
            try:
                self._onscreen_image.destroy()
            except Exception:
                pass
