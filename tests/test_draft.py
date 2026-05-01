import json
import tempfile
import unittest
from pathlib import Path

from mcp_cut import draft
from mcp_cut import paths


class DraftMediaStagingTests(unittest.TestCase):
    def test_add_media_stages_external_files_inside_draft_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_paths_root = paths.CAPCUT_PROJECTS_ROOT
            original_draft_root = draft.CAPCUT_PROJECTS_ROOT
            paths.CAPCUT_PROJECTS_ROOT = Path(tmp) / "drafts"
            draft.CAPCUT_PROJECTS_ROOT = paths.CAPCUT_PROJECTS_ROOT
            try:
                source_dir = Path(tmp) / "source"
                source_dir.mkdir()
                video = source_dir / "clip.mp4"
                audio = source_dir / "voice.mp3"
                video.write_bytes(b"fake video")
                audio.write_bytes(b"fake audio")

                draft.create_draft("staging-test", width=1080, height=1920, fps=30)
                draft.add_video(
                    "staging-test",
                    str(video),
                    duration_seconds=3,
                    width=1080,
                    height=1920,
                    has_audio=False,
                )
                draft.add_audio("staging-test", str(audio), duration_seconds=3)

                folder = paths.CAPCUT_PROJECTS_ROOT / "staging-test"
                info = json.loads((folder / "draft_info.json").read_text())
                media_paths = [
                    item["path"]
                    for category in ("videos", "audios")
                    for item in info["materials"][category]
                ]

                self.assertEqual(len(media_paths), 2)
                for media_path in media_paths:
                    staged = Path(media_path)
                    self.assertTrue(staged.exists())
                    self.assertEqual(
                        staged.parent.resolve(),
                        (folder / "mcp_cut_media").resolve(),
                    )
                    self.assertNotEqual(staged.parent.resolve(), source_dir.resolve())
            finally:
                paths.CAPCUT_PROJECTS_ROOT = original_paths_root
                draft.CAPCUT_PROJECTS_ROOT = original_draft_root


if __name__ == "__main__":
    unittest.main()
