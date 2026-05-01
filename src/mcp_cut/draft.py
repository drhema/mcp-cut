"""CapCut macOS draft (`draft_info.json` + `draft_meta_info.json`) generator.

Schema mirrored from a real CapCut draft on macOS (CapCut 7.7.7-beta2,
draft new_version 151.0.0, version 360000). Time units are microseconds.
"""

from __future__ import annotations

import json
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Iterable, Iterator

from .paths import CAPCUT_PROJECTS_ROOT, draft_dir, ensure_root

US_PER_S = 1_000_000
PHOTO_LONG_DURATION_US = 10_800_000_000_000  # CapCut's pseudo-infinite for stills


class DraftError(Exception):
    pass


def _uuid() -> str:
    return str(uuid.uuid4()).upper()


def _now_us() -> int:
    return int(time.time() * US_PER_S)


# ---- platform block ---------------------------------------------------------

# CapCut stores device fingerprints in `last_modified_platform` and
# `platform`. The values are stable identifiers but not validated, so any
# consistent strings work. We use zeroed placeholders here — CapCut will
# overwrite them with the host's real values on first save.
PLATFORM = {
    "app_id": 359289,
    "app_source": "cc",
    "app_version": "8.5.0",
    "device_id": "00000000000000000000000000000000",
    "hard_disk_id": "00000000000000000000000000000000",
    "mac_address": "00000000000000000000000000000000",
    "os": "mac",
    "os_version": "0.0",
}


# ---- auxiliary materials ----------------------------------------------------
# Each segment references a fixed set of auxiliary materials by ID. We
# generate fresh ones per segment and append to the global `materials` bucket.

def _make_speed() -> dict[str, Any]:
    return {"curve_speed": None, "id": _uuid(), "mode": 0, "speed": 1.0, "type": "speed"}


def _make_placeholder_info() -> dict[str, Any]:
    return {
        "error_path": "", "error_text": "", "id": _uuid(),
        "meta_type": "none", "res_path": "", "res_text": "",
        "type": "placeholder_info",
    }


def _make_canvas() -> dict[str, Any]:
    return {
        "album_image": "", "blur": 0.0, "color": "", "id": _uuid(),
        "image": "", "image_id": "", "image_name": "",
        "source_platform": 0, "team_id": "", "type": "canvas_color",
    }


def _make_sound_channel_mapping() -> dict[str, Any]:
    return {"audio_channel_mapping": 0, "id": _uuid(), "is_config_open": False, "type": ""}


def _make_material_color() -> dict[str, Any]:
    return {
        "gradient_angle": 90.0, "gradient_colors": [], "gradient_percents": [],
        "height": 0.0, "id": _uuid(), "is_color_clip": False, "is_gradient": False,
        "solid_color": "", "width": 0.0,
    }


def _make_vocal_separation() -> dict[str, Any]:
    return {
        "choice": 0, "enter_from": "", "final_algorithm": "",
        "id": _uuid(), "production_path": "", "removed_sounds": [],
        "time_range": None, "type": "vocal_separation",
    }


def _make_beats() -> dict[str, Any]:
    return {
        "ai_beats": {
            "beat_speed_infos": [], "beats_path": "", "beats_url": "",
            "melody_path": "", "melody_percents": [0.0], "melody_url": "",
        },
        "enable_ai_beats": False, "gear": 404, "gear_count": 0,
        "id": _uuid(), "mode": 404, "type": "beats",
        "user_beats": [], "user_delete_ai_beats": None,
    }


# ---- visual (image / video) materials ---------------------------------------

def _make_visual_material(
    *,
    media_type: str,             # "photo" or "video"
    path: str,
    duration_us: int,
    width: int,
    height: int,
    has_audio: bool,
) -> dict[str, Any]:
    return {
        "aigc_history_id": "", "aigc_item_id": "", "aigc_type": "none",
        "audio_fade": None,
        "beauty_body_auto_preset": None, "beauty_body_preset_id": "",
        "beauty_face_auto_preset": {"name": "", "preset_id": "", "rate_map": "", "scene": ""},
        "beauty_face_auto_preset_infos": [], "beauty_face_preset_infos": [],
        "cartoon_path": "",
        "category_id": "", "category_name": "",
        "check_flag": 62978047,
        "content_feature_info": None,
        "corner_pin": None,
        "crop": {
            "lower_left_x": 0.0, "lower_left_y": 1.0,
            "lower_right_x": 1.0, "lower_right_y": 1.0,
            "upper_left_x": 0.0, "upper_left_y": 0.0,
            "upper_right_x": 1.0, "upper_right_y": 0.0,
        },
        "crop_ratio": "free", "crop_scale": 1.0,
        "duration": duration_us,
        "extra_type_option": 0, "formula_id": "", "freeze": None,
        "has_audio": has_audio, "has_sound_separated": False,
        "height": height,
        "id": _uuid(),
        "intensifies_audio_path": "", "intensifies_path": "",
        "is_ai_generate_content": False, "is_copyright": True,
        "is_text_edit_overdub": False, "is_unified_beauty_mode": False,
        "live_photo_cover_path": "", "live_photo_timestamp": -1,
        "local_id": "", "local_material_from": "", "local_material_id": "",
        "material_id": "", "material_name": Path(path).name, "material_url": "",
        "matting": {
            "custom_matting_id": "", "enable_matting_stroke": False,
            "expansion": 0, "feather": 0, "flag": 0,
            "has_use_quick_brush": False, "has_use_quick_eraser": False,
            "interactiveTime": [], "path": "", "reverse": False, "strokes": [],
        },
        "media_path": "", "multi_camera_info": None, "object_locked": None,
        "origin_material_id": "",
        "path": path,
        "picture_from": "none",
        "picture_set_category_id": "", "picture_set_category_name": "",
        "request_id": "", "reverse_intensifies_path": "", "reverse_path": "",
        "smart_match_info": None, "smart_motion": None,
        "source": 0, "source_platform": 0,
        "stable": {"matrix_path": "", "stable_level": 0,
                   "time_range": {"duration": 0, "start": 0}},
        "team_id": "",
        "type": media_type,
        "video_algorithm": {
            "ai_background_configs": [], "ai_expression_driven": None,
            "ai_in_painting_config": [], "ai_motion_driven": None,
            "aigc_generate": None, "aigc_generate_list": [],
            "algorithms": [], "complement_frame_config": None,
            "deflicker": None, "gameplay_configs": [],
            "image_interpretation": None, "motion_blur_config": None,
            "mouth_shape_driver": None, "noise_reduction": None,
            "path": "", "quality_enhance": None,
            "skip_algorithm_index": [], "smart_complement_frame": None,
            "story_video_modify_video_config": {
                "is_overwrite_last_video": False, "task_id": "", "tracker_task_id": "",
            },
            "super_resolution": None,
            "time_range": {"duration": 0, "start": 0},
        },
        "width": width,
    }


def _make_audio_material(audio_path: str, duration_us: int) -> dict[str, Any]:
    return {
        "ai_music_generate_scene": 0, "ai_music_type": 0,
        "aigc_history_id": "", "aigc_item_id": "",
        "app_id": 0, "category_id": "", "category_name": "",
        "check_flag": 1, "cloned_model_type": "", "copyright_limit_type": "none",
        "duration": duration_us,
        "effect_id": "", "formula_id": "",
        "id": _uuid(),
        "intensifies_path": "",
        "is_ai_clone_tone": False, "is_ai_clone_tone_post": False,
        "is_text_edit_overdub": False, "is_ugc": False,
        "local_material_id": "", "lyric_type": 0,
        "mock_tone_speaker": "", "moyin_emotion": "",
        "music_id": "", "music_source": "",
        "name": Path(audio_path).name, "path": audio_path,
        "pgc_id": "", "pgc_name": "", "query": "", "request_id": "",
        "resource_id": "", "search_id": "",
        "similiar_music_info": {"original_song_id": "", "original_song_name": ""},
        "sound_separate_type": "", "source_from": "", "source_platform": 0,
        "team_id": "", "text_id": "", "third_resource_id": "",
        "tone_category_id": "", "tone_category_name": "",
        "tone_effect_id": "", "tone_effect_name": "",
        "tone_emotion_name_key": "", "tone_emotion_role": "",
        "tone_emotion_scale": 0.0, "tone_emotion_selection": "",
        "tone_emotion_style": "", "tone_platform": "",
        "tone_second_category_id": "", "tone_second_category_name": "",
        "tone_speaker": "", "tone_type": "",
        "tts_generate_scene": "", "tts_task_id": "",
        "type": "extract_music", "video_id": "", "wave_points": [],
    }


# ---- segments ---------------------------------------------------------------

def _video_segment(
    *,
    material_id: str,
    target_start_us: int,
    target_dur_us: int,
    source_start_us: int,
    track_render_index: int,
    extra_refs: list[str],
    transform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clip = transform or {
        "alpha": 1.0,
        "flip": {"horizontal": False, "vertical": False},
        "rotation": 0.0,
        "scale": {"x": 1.0, "y": 1.0},
        "transform": {"x": 0.0, "y": 0.0},
    }
    return {
        "caption_info": None, "cartoon": False,
        "clip": clip,
        "color_correct_alg_result": "",
        "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": True, "enable_adjust_mask": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False, "enable_hsl_curves": True,
        "enable_lut": True, "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "",
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "id": _uuid(),
        "intensifies_audio": False,
        "is_loop": False, "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "", "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": {"duration": target_dur_us, "start": source_start_us},
        "speed": 1.0, "state": 0,
        "target_timerange": {"duration": target_dur_us, "start": target_start_us},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": track_render_index,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True, "volume": 1.0,
    }


def _audio_segment(
    *,
    material_id: str,
    target_start_us: int,
    target_dur_us: int,
    source_start_us: int,
    track_render_index: int,
    extra_refs: list[str],
) -> dict[str, Any]:
    return {
        "caption_info": None, "cartoon": False, "clip": None,
        "color_correct_alg_result": "",
        "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False, "enable_hsl_curves": True,
        "enable_lut": False, "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "", "hdr_settings": None,
        "id": _uuid(),
        "intensifies_audio": False,
        "is_loop": False, "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "", "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": {"duration": target_dur_us, "start": source_start_us},
        "speed": 1.0, "state": 0,
        "target_timerange": {"duration": target_dur_us, "start": target_start_us},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": track_render_index,
        "uniform_scale": None,
        "visible": True, "volume": 1.0,
    }


# ---- empty draft ------------------------------------------------------------

def _empty_materials() -> dict[str, list]:
    return {
        "ai_translates": [], "audio_balances": [], "audio_effects": [],
        "audio_fades": [], "audio_pannings": [], "audio_pitch_shifts": [],
        "audio_track_indexes": [],
        "audios": [], "beats": [], "canvases": [], "chromas": [],
        "color_curves": [], "common_mask": [],
        "digital_human_model_dressing": [], "digital_humans": [],
        "drafts": [], "effects": [], "flowers": [], "green_screens": [],
        "handwrites": [], "hsl": [], "hsl_curves": [], "images": [],
        "log_color_wheels": [], "loudnesses": [], "manual_beautys": [],
        "manual_deformations": [], "material_animations": [],
        "material_colors": [], "multi_language_refs": [],
        "placeholder_infos": [], "placeholders": [], "plugin_effects": [],
        "primary_color_wheels": [], "realtime_denoises": [], "shapes": [],
        "smart_crops": [], "smart_relights": [],
        "sound_channel_mappings": [], "speeds": [], "stickers": [],
        "tail_leaders": [], "text_templates": [], "texts": [],
        "time_marks": [], "transitions": [], "video_effects": [],
        "video_radius": [], "video_shadows": [], "video_strokes": [],
        "video_trackings": [], "videos": [],
        "vocal_beautifys": [], "vocal_separations": [],
    }


def _empty_track(type_: str) -> dict[str, Any]:
    return {
        "attribute": 0, "flag": 0, "id": _uuid(),
        "is_default_name": True, "name": "", "segments": [],
        "type": type_,
    }


def _empty_draft_info(width: int, height: int, fps: float) -> dict[str, Any]:
    return {
        "canvas_config": {"background": None, "height": height, "ratio": "original", "width": width},
        "color_space": 0,
        "config": {
            "adjust_max_index": 1, "attachment_info": [],
            "combination_max_index": 1, "export_range": None,
            "extract_audio_last_index": 1,
            "lyrics_recognition_id": "", "lyrics_sync": True, "lyrics_taskinfo": [],
            "maintrack_adsorb": True, "material_save_mode": 0,
            "multi_language_current": "none", "multi_language_list": [],
            "multi_language_main": "none", "multi_language_mode": "none",
            "original_sound_last_index": 1, "record_audio_last_index": 1,
            "sticker_max_index": 1,
            "subtitle_keywords_config": None,
            "subtitle_recognition_id": "", "subtitle_sync": True,
            "subtitle_taskinfo": [], "system_font_list": [],
            "use_float_render": False, "video_mute": False,
            "zoom_info_params": None,
        },
        "cover": None, "create_time": 0,
        "draft_type": "video", "duration": 0,
        "extra_info": None, "fps": fps,
        "free_render_index_mode_on": False,
        "function_assistant_info": {
            "audio_noise_segid_list": [], "auto_adjust": False,
            "auto_adjust_fixed": False, "auto_adjust_fixed_value": 50.0,
            "auto_adjust_segid_list": [], "auto_caption": False,
            "auto_caption_segid_list": [], "auto_caption_template_id": "",
            "caption_opt": False, "caption_opt_segid_list": [],
            "color_correction": False, "color_correction_fixed": False,
            "color_correction_fixed_value": 50.0,
            "color_correction_segid_list": [],
            "deflicker_segid_list": [], "enhance_quality": False,
            "enhance_quality_fixed": False, "enhance_quality_segid_list": [],
            "enhance_voice_segid_list": [], "enhande_voice": False,
            "enhande_voice_fixed": False, "eye_correction": False,
            "eye_correction_segid_list": [], "fixed_rec_applied": False,
            "fps": {"den": 1, "num": 0}, "normalize_loudness": False,
            "normalize_loudness_audio_denoise_segid_list": [],
            "normalize_loudness_fixed": False,
            "normalize_loudness_segid_list": [], "retouch": False,
            "retouch_fixed": False, "retouch_segid_list": [],
            "smart_rec_applied": False, "smart_segid_list": [],
            "smooth_slow_motion": False, "smooth_slow_motion_fixed": False,
            "video_noise_segid_list": [],
        },
        "group_container": None,
        "id": _uuid(),
        "is_drop_frame_timecode": False,
        "keyframe_graph_list": [],
        "keyframes": {
            "adjusts": [], "audios": [], "effects": [], "filters": [],
            "handwrites": [], "stickers": [], "texts": [], "videos": [],
        },
        "last_modified_platform": dict(PLATFORM),
        "lyrics_effects": [],
        "materials": _empty_materials(),
        "mutable_config": None,
        "name": "",
        "new_version": "167.0.0",
        "path": "",
        "platform": dict(PLATFORM),
        "relationships": [],
        "render_index_track_mode_on": True,
        "retouch_cover": None,
        "smart_ads_info": {"draft_url": "", "page_from": "", "routine": ""},
        "source": "default",
        "static_cover_image_path": "",
        "time_marks": None,
        "tracks": [_empty_track("video"), _empty_track("audio")],
        "uneven_animation_template_info": {
            "composition": "", "content": "", "order": "",
            "sub_template_info_list": [],
        },
        "update_time": 0,
        "version": 360000,
    }


def _empty_meta_info(name: str, fold_path: Path, root_path: Path) -> dict[str, Any]:
    now_us = _now_us()
    return {
        "cloud_draft_cover": True, "cloud_draft_sync": True,
        "cloud_package_completed_time": "",
        "draft_cloud_capcut_purchase_info": "",
        "draft_cloud_last_action_download": False,
        "draft_cloud_package_type": "",
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg",
        "draft_deeplink_url": "",
        "draft_enterprise_info": {
            "draft_enterprise_extra": "", "draft_enterprise_id": "",
            "draft_enterprise_name": "", "enterprise_material": [],
        },
        "draft_fold_path": str(fold_path),
        "draft_id": _uuid(),
        "draft_is_ae_produce": False,
        "draft_is_ai_packaging_used": False,
        "draft_is_ai_shorts": False, "draft_is_ai_translate": False,
        "draft_is_article_video_draft": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_from_deeplink": "false",
        "draft_is_invisible": False, "draft_is_web_article_video": False,
        "draft_materials": [
            {"type": 0, "value": []}, {"type": 1, "value": []},
            {"type": 2, "value": []}, {"type": 3, "value": []},
            {"type": 6, "value": []}, {"type": 7, "value": []},
            {"type": 8, "value": []},
        ],
        "draft_materials_copied_info": [],
        "draft_name": name,
        "draft_need_rename_folder": False,
        "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": str(root_path),
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": 0,
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": 0,
    }


# ---- I/O --------------------------------------------------------------------

def _read_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(p: Path, data: dict[str, Any]) -> None:
    p.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def _info_path(d: Path) -> Path:
    return d / "draft_info.json"


def _meta_path(d: Path) -> Path:
    return d / "draft_meta_info.json"


def _load(name: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    folder = draft_dir(name)
    if not folder.exists():
        raise DraftError(f"Draft not found: {folder}")
    return folder, _read_json(_info_path(folder)), _read_json(_meta_path(folder))


def _save(folder: Path, info: dict[str, Any], meta: dict[str, Any]) -> None:
    _bump_modified(meta, info)
    _write_json(_info_path(folder), info)
    _write_json(_meta_path(folder), meta)


def _bump_modified(meta: dict[str, Any], info: dict[str, Any]) -> None:
    meta["tm_draft_modified"] = _now_us()
    end = 0
    for tr in info["tracks"]:
        for seg in tr["segments"]:
            t = seg["target_timerange"]
            end = max(end, t["start"] + t["duration"])
    meta["tm_duration"] = end
    info["duration"] = end


# ---- track helpers ----------------------------------------------------------

def _tracks_of_type(info: dict[str, Any], type_: str) -> list[dict[str, Any]]:
    return [t for t in info["tracks"] if t["type"] == type_]


def _get_or_create_track(info: dict[str, Any], type_: str, index: int) -> dict[str, Any]:
    if index < 0:
        raise DraftError(f"track index must be >= 0, got {index}")
    matches = _tracks_of_type(info, type_)
    while len(matches) <= index:
        info["tracks"].append(_empty_track(type_))
        matches = _tracks_of_type(info, type_)
    return matches[index]


def _track_render_index(info: dict[str, Any], track: dict[str, Any]) -> int:
    return info["tracks"].index(track)


def _next_start_on_track(track: dict[str, Any]) -> int:
    end = 0
    for seg in track["segments"]:
        t = seg["target_timerange"]
        end = max(end, t["start"] + t["duration"])
    return end


def _find_segment(info: dict[str, Any], segment_id: str) -> dict[str, Any]:
    for tr in info["tracks"]:
        for seg in tr["segments"]:
            if seg["id"] == segment_id:
                return seg
    raise DraftError(f"segment not found: {segment_id}")


# ---- public API -------------------------------------------------------------

def list_drafts() -> list[dict[str, Any]]:
    root = CAPCUT_PROJECTS_ROOT
    if not root.exists():
        return []
    out: list[dict[str, Any]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        info_p = child / "draft_info.json"
        if not info_p.exists():
            continue
        try:
            info = _read_json(info_p)
            out.append({
                "name": child.name,
                "path": str(child),
                "duration_seconds": info.get("duration", 0) / US_PER_S,
                "fps": info.get("fps"),
                "canvas": info.get("canvas_config", {}),
            })
        except Exception as e:
            out.append({"name": child.name, "path": str(child), "error": str(e)})
    return out


def inspect_draft(name: str) -> dict[str, Any]:
    folder, info, meta = _load(name)
    tracks_summary = []
    for idx, tr in enumerate(info["tracks"]):
        tracks_summary.append({
            "track_index": idx,
            "type": tr["type"],
            "segment_count": len(tr["segments"]),
            "segments": [
                {
                    "id": seg["id"],
                    "material_id": seg["material_id"],
                    "start_seconds": seg["target_timerange"]["start"] / US_PER_S,
                    "duration_seconds": seg["target_timerange"]["duration"] / US_PER_S,
                    "volume": seg.get("volume", 1.0),
                    "transform": seg.get("clip"),
                }
                for seg in tr["segments"]
            ],
        })
    return {
        "name": name,
        "path": str(folder),
        "duration_seconds": info["duration"] / US_PER_S,
        "fps": info["fps"],
        "canvas": info["canvas_config"],
        "tracks": tracks_summary,
        "modified": meta["tm_draft_modified"],
    }


def create_draft(name: str, width: int, height: int, fps: float) -> Path:
    root = ensure_root()
    folder = draft_dir(name)
    if folder.exists():
        raise DraftError(f"Draft folder already exists: {folder}")
    folder.mkdir(parents=True)

    info = _empty_draft_info(width, height, fps)
    meta = _empty_meta_info(name, folder, root)

    _write_json(_info_path(folder), info)
    _write_json(_meta_path(folder), meta)
    return folder


def delete_draft(name: str) -> dict[str, Any]:
    folder = draft_dir(name)
    if not folder.exists():
        raise DraftError(f"Draft not found: {folder}")
    shutil.rmtree(folder)
    return {"deleted": str(folder)}


def _add_visual(
    *,
    name: str,
    path: str,
    media_type: str,
    duration_seconds: float,
    source_start_seconds: float,
    has_audio: bool,
    width: int,
    height: int,
    start_seconds: float | None,
    track_index: int,
) -> dict[str, Any]:
    abs_path = str(Path(path).expanduser().resolve())
    if not Path(abs_path).exists():
        raise DraftError(f"File not found: {abs_path}")

    folder, info, meta = _load(name)

    target_dur = int(duration_seconds * US_PER_S)
    source_start = int(source_start_seconds * US_PER_S)

    mat_dur = PHOTO_LONG_DURATION_US if media_type == "photo" else max(target_dur + source_start, target_dur)
    mat = _make_visual_material(
        media_type=media_type,
        path=abs_path,
        duration_us=mat_dur,
        width=width,
        height=height,
        has_audio=has_audio,
    )
    info["materials"]["videos"].append(mat)

    speed = _make_speed()
    placeholder = _make_placeholder_info()
    canvas = _make_canvas()
    scm = _make_sound_channel_mapping()
    color = _make_material_color()
    vsep = _make_vocal_separation()
    info["materials"]["speeds"].append(speed)
    info["materials"]["placeholder_infos"].append(placeholder)
    info["materials"]["canvases"].append(canvas)
    info["materials"]["sound_channel_mappings"].append(scm)
    info["materials"]["material_colors"].append(color)
    info["materials"]["vocal_separations"].append(vsep)

    track = _get_or_create_track(info, "video", track_index)
    target_start = int(start_seconds * US_PER_S) if start_seconds is not None else _next_start_on_track(track)

    seg = _video_segment(
        material_id=mat["id"],
        target_start_us=target_start,
        target_dur_us=target_dur,
        source_start_us=source_start,
        track_render_index=_track_render_index(info, track),
        extra_refs=[speed["id"], placeholder["id"], canvas["id"], scm["id"], color["id"], vsep["id"]],
    )
    track["segments"].append(seg)

    _save(folder, info, meta)
    return {
        "material_id": mat["id"],
        "segment_id": seg["id"],
        "track_index": track_index,
        "start_seconds": target_start / US_PER_S,
        "duration_seconds": target_dur / US_PER_S,
    }


def add_image(
    name: str,
    image_path: str,
    duration_seconds: float,
    width: int = 1920,
    height: int = 1080,
    start_seconds: float | None = None,
    track_index: int = 0,
) -> dict[str, Any]:
    return _add_visual(
        name=name, path=image_path, media_type="photo",
        duration_seconds=duration_seconds, source_start_seconds=0.0,
        has_audio=False, width=width, height=height,
        start_seconds=start_seconds, track_index=track_index,
    )


def add_video(
    name: str,
    video_path: str,
    duration_seconds: float,
    width: int,
    height: int,
    source_start_seconds: float = 0.0,
    has_audio: bool = True,
    start_seconds: float | None = None,
    track_index: int = 0,
) -> dict[str, Any]:
    return _add_visual(
        name=name, path=video_path, media_type="video",
        duration_seconds=duration_seconds,
        source_start_seconds=source_start_seconds,
        has_audio=has_audio, width=width, height=height,
        start_seconds=start_seconds, track_index=track_index,
    )


def add_image_sequence(
    name: str,
    image_paths: Iterable[str],
    frame_seconds: float = 0.1,
    start_seconds: float | None = None,
    track_index: int = 0,
    width: int = 1920,
    height: int = 1080,
) -> dict[str, Any]:
    """Append images one after another at `frame_seconds` each — the
    frame-by-frame cartoon technique from method.md (default 0.1s = 10fps)."""
    paths = list(image_paths)
    if not paths:
        raise DraftError("image_paths is empty")
    results = []
    cursor = start_seconds
    for p in paths:
        r = add_image(
            name=name, image_path=p,
            duration_seconds=frame_seconds,
            width=width, height=height,
            start_seconds=cursor,
            track_index=track_index,
        )
        results.append(r)
        # Subsequent frames stack — let _next_start_on_track resolve.
        cursor = None
    return {
        "frame_count": len(results),
        "first_segment_id": results[0]["segment_id"],
        "last_segment_id": results[-1]["segment_id"],
        "total_duration_seconds": len(results) * frame_seconds,
    }


def add_audio(
    name: str,
    audio_path: str,
    duration_seconds: float,
    start_seconds: float = 0.0,
    source_start_seconds: float = 0.0,
    track_index: int = 0,
) -> dict[str, Any]:
    abs_path = str(Path(audio_path).expanduser().resolve())
    if not Path(abs_path).exists():
        raise DraftError(f"Audio file not found: {abs_path}")

    folder, info, meta = _load(name)

    target_dur = int(duration_seconds * US_PER_S)
    source_start = int(source_start_seconds * US_PER_S)
    mat = _make_audio_material(abs_path, target_dur + source_start)
    info["materials"]["audios"].append(mat)

    speed = _make_speed()
    placeholder = _make_placeholder_info()
    beats = _make_beats()
    scm = _make_sound_channel_mapping()
    vsep = _make_vocal_separation()
    info["materials"]["speeds"].append(speed)
    info["materials"]["placeholder_infos"].append(placeholder)
    info["materials"]["beats"].append(beats)
    info["materials"]["sound_channel_mappings"].append(scm)
    info["materials"]["vocal_separations"].append(vsep)

    track = _get_or_create_track(info, "audio", track_index)
    target_start = int(start_seconds * US_PER_S)

    seg = _audio_segment(
        material_id=mat["id"],
        target_start_us=target_start,
        target_dur_us=target_dur,
        source_start_us=source_start,
        track_render_index=_track_render_index(info, track),
        extra_refs=[speed["id"], placeholder["id"], beats["id"], scm["id"], vsep["id"]],
    )
    track["segments"].append(seg)

    _save(folder, info, meta)
    return {
        "material_id": mat["id"],
        "segment_id": seg["id"],
        "track_index": track_index,
        "start_seconds": target_start / US_PER_S,
        "duration_seconds": target_dur / US_PER_S,
    }


def set_clip_transform(
    name: str,
    segment_id: str,
    x: float | None = None,
    y: float | None = None,
    scale_x: float | None = None,
    scale_y: float | None = None,
    rotation: float | None = None,
    alpha: float | None = None,
    flip_horizontal: bool | None = None,
    flip_vertical: bool | None = None,
) -> dict[str, Any]:
    """Set position/scale/rotation/alpha on a video segment.

    Coordinates are CapCut's normalized space: x/y in roughly [-1, 1] where
    (0,0) is canvas center; scale is a multiplier (1.0 = native);
    rotation in degrees; alpha in [0, 1].
    """
    folder, info, meta = _load(name)
    seg = _find_segment(info, segment_id)
    clip = seg.get("clip")
    if clip is None:
        raise DraftError(f"segment {segment_id} has no clip block (audio segment?)")

    if x is not None:
        clip["transform"]["x"] = float(x)
    if y is not None:
        clip["transform"]["y"] = float(y)
    if scale_x is not None:
        clip["scale"]["x"] = float(scale_x)
    if scale_y is not None:
        clip["scale"]["y"] = float(scale_y)
    if rotation is not None:
        clip["rotation"] = float(rotation)
    if alpha is not None:
        clip["alpha"] = float(alpha)
    if flip_horizontal is not None:
        clip["flip"]["horizontal"] = bool(flip_horizontal)
    if flip_vertical is not None:
        clip["flip"]["vertical"] = bool(flip_vertical)

    _save(folder, info, meta)
    return {"segment_id": segment_id, "clip": clip}


def set_segment_volume(name: str, segment_id: str, volume: float) -> dict[str, Any]:
    """Set the volume on a video or audio segment (1.0 = unchanged)."""
    folder, info, meta = _load(name)
    seg = _find_segment(info, segment_id)
    seg["volume"] = float(volume)
    if volume > 0:
        seg["last_nonzero_volume"] = float(volume)
    _save(folder, info, meta)
    return {"segment_id": segment_id, "volume": volume}


# ---- segment editing --------------------------------------------------------

def move_segment(name: str, segment_id: str, start_seconds: float) -> dict[str, Any]:
    folder, info, meta = _load(name)
    seg = _find_segment(info, segment_id)
    seg["target_timerange"]["start"] = int(start_seconds * US_PER_S)
    _save(folder, info, meta)
    return {"segment_id": segment_id, "start_seconds": start_seconds}


def trim_segment(
    name: str,
    segment_id: str,
    duration_seconds: float | None = None,
    source_start_seconds: float | None = None,
) -> dict[str, Any]:
    """Adjust the timeline duration and/or source-trim of a segment."""
    folder, info, meta = _load(name)
    seg = _find_segment(info, segment_id)
    if duration_seconds is not None:
        new_dur = int(duration_seconds * US_PER_S)
        seg["target_timerange"]["duration"] = new_dur
        if seg.get("source_timerange") is not None:
            seg["source_timerange"]["duration"] = new_dur
    if source_start_seconds is not None and seg.get("source_timerange") is not None:
        seg["source_timerange"]["start"] = int(source_start_seconds * US_PER_S)
    _save(folder, info, meta)
    return {
        "segment_id": segment_id,
        "duration_seconds": seg["target_timerange"]["duration"] / US_PER_S,
    }


def delete_segment(name: str, segment_id: str) -> dict[str, Any]:
    folder, info, meta = _load(name)
    for tr in info["tracks"]:
        for i, seg in enumerate(tr["segments"]):
            if seg["id"] == segment_id:
                del tr["segments"][i]
                _save(folder, info, meta)
                return {"deleted": segment_id}
    raise DraftError(f"segment not found: {segment_id}")


def _gc_orphan_materials(info: dict[str, Any]) -> dict[str, int]:
    """Remove material entries no longer referenced by any segment.

    CapCut tolerates orphans up to a point but accumulating hundreds of
    them across iterations seems to confuse the loader. We GC after every
    clear so re-running captions doesn't pile up dead materials.
    """
    referenced: set[str] = set()
    for tr in info["tracks"]:
        for seg in tr["segments"]:
            referenced.add(seg.get("material_id", ""))
            referenced.update(seg.get("extra_material_refs", []) or [])
    removed: dict[str, int] = {}
    for cat, items in info["materials"].items():
        if not isinstance(items, list):
            continue
        keep: list[Any] = []
        gone = 0
        for it in items:
            if isinstance(it, dict) and it.get("id") in referenced:
                keep.append(it)
            elif isinstance(it, dict):
                gone += 1
            else:
                keep.append(it)
        if gone:
            info["materials"][cat] = keep
            removed[cat] = gone
    return removed


def clear_track(name: str, track_type: str, track_index: int = 0) -> dict[str, Any]:
    """Remove every segment from one track and garbage-collect any
    materials that become orphaned as a result.

    Use to iterate on captions in the same draft: `clear_track("text")`,
    then re-run `add_captions_from_srt` with different style/font/position.
    """
    folder, info, meta = _load(name)
    matches = _tracks_of_type(info, track_type)
    if track_index >= len(matches):
        return {"cleared": 0, "track_type": track_type, "track_index": track_index,
                "reason": f"no {track_type} track at index {track_index}"}
    track = matches[track_index]
    n = len(track["segments"])
    track["segments"] = []
    gc = _gc_orphan_materials(info)
    _save(folder, info, meta)
    return {"cleared": n, "track_type": track_type, "track_index": track_index,
            "materials_gc": gc}


def clear_text_tracks(name: str) -> dict[str, Any]:
    """Remove all segments from every text track and GC orphan materials.

    Convenience for re-running captions on the same draft.
    """
    folder, info, meta = _load(name)
    total = 0
    for tr in info["tracks"]:
        if tr["type"] == "text":
            total += len(tr["segments"])
            tr["segments"] = []
    gc = _gc_orphan_materials(info)
    _save(folder, info, meta)
    return {"cleared": total, "materials_gc": gc}


# ---- keyframes --------------------------------------------------------------

KEYFRAME_PROPERTY_MAP = {
    "x": "KFTypePositionX",
    "y": "KFTypePositionY",
    "scale_x": "KFTypeScaleX",
    "scale_y": "KFTypeScaleY",
    "rotation": "KFTypeRotation",
    "alpha": "KFTypeAlpha",
    "volume": "KFTypeVolume",
}


def add_keyframe(
    name: str,
    segment_id: str,
    time_seconds: float,
    property: str,
    value: float,
    curve: str = "Line",
) -> dict[str, Any]:
    """Add a keyframe to a segment.

    `time_seconds` is absolute timeline time (CapCut uses time relative to
    segment start internally — we convert).
    `property` is one of: x, y, scale_x, scale_y, rotation, alpha, volume.
    `curve` is "Line" (default) or "Bezier".
    """
    if property not in KEYFRAME_PROPERTY_MAP:
        raise DraftError(f"property must be one of {sorted(KEYFRAME_PROPERTY_MAP)}")
    prop_type = KEYFRAME_PROPERTY_MAP[property]

    folder, info, meta = _load(name)
    seg = _find_segment(info, segment_id)

    seg_start = seg["target_timerange"]["start"]
    seg_dur = seg["target_timerange"]["duration"]
    abs_us = int(time_seconds * US_PER_S)
    rel_us = abs_us - seg_start
    if rel_us < 0 or rel_us > seg_dur:
        raise DraftError(
            f"time {time_seconds}s is outside segment range "
            f"[{seg_start / US_PER_S}, {(seg_start + seg_dur) / US_PER_S}]s"
        )

    groups = seg.setdefault("common_keyframes", [])
    group = next((g for g in groups if g["property_type"] == prop_type), None)
    if group is None:
        group = {
            "id": _uuid(),
            "keyframe_list": [],
            "material_id": "",
            "property_type": prop_type,
        }
        groups.append(group)

    kf = {
        "curveType": curve,
        "graphID": "",
        "id": _uuid(),
        "left_control": {"x": 0.0, "y": 0.0},
        "right_control": {"x": 0.0, "y": 0.0},
        "time_offset": rel_us,
        "values": [float(value)],
    }
    group["keyframe_list"].append(kf)
    group["keyframe_list"].sort(key=lambda k: k["time_offset"])

    _save(folder, info, meta)
    return {
        "segment_id": segment_id,
        "property": property,
        "time_seconds": time_seconds,
        "value": value,
        "keyframe_id": kf["id"],
    }


# ---- text -------------------------------------------------------------------

def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


# System fonts shipped with CapCut on macOS. CapCut won't render text
# without a real font_path. CapCutSansText is CapCut's branded sans;
# Noto* are the per-script Unicode fonts.
_CAPCUT_FONT_DIR = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont"
_FONTS_BY_LANG = {
    "en": f"{_CAPCUT_FONT_DIR}/CapCutSansText-Regular.otf",
    "en-bold": f"{_CAPCUT_FONT_DIR}/CapCutSansText-Bold.otf",
    "en-medium": f"{_CAPCUT_FONT_DIR}/CapCutSansText-Medium.otf",
    "ar": f"{_CAPCUT_FONT_DIR}/NotoSansArabic-Regular.ttf",
    "ja": f"{_CAPCUT_FONT_DIR}/ja.ttf",
    "ko": f"{_CAPCUT_FONT_DIR}/ko.ttf",
    "th": f"{_CAPCUT_FONT_DIR}/th.ttf",
    "zh": f"{_CAPCUT_FONT_DIR}/zh-hans.ttf",
    "zh-hant": f"{_CAPCUT_FONT_DIR}/zh-hant.ttf",
    "he": f"{_CAPCUT_FONT_DIR}/NotoSansHebrew-Regular.ttf",
    "bn": f"{_CAPCUT_FONT_DIR}/NotoSansBengali-Regular.ttf",
}
_CAPCUT_DEFAULT_FONT = _FONTS_BY_LANG["en"]


def _detect_font_for(text: str, *, bold: bool = False) -> str:
    """Pick a font path based on script ranges. Bold variant for Latin only
    (CapCut doesn't ship bold for the per-script Noto fonts)."""
    for ch in text:
        c = ord(ch)
        if 0x0600 <= c <= 0x06FF or 0x0750 <= c <= 0x077F:
            return _FONTS_BY_LANG["ar"]
        if 0x0590 <= c <= 0x05FF:
            return _FONTS_BY_LANG["he"]
        if 0x3040 <= c <= 0x30FF:
            return _FONTS_BY_LANG["ja"]
        if 0xAC00 <= c <= 0xD7AF:
            return _FONTS_BY_LANG["ko"]
        if 0x4E00 <= c <= 0x9FFF:
            return _FONTS_BY_LANG["zh"]
        if 0x0E00 <= c <= 0x0E7F:
            return _FONTS_BY_LANG["th"]
    return _FONTS_BY_LANG["en-bold"] if bold else _CAPCUT_DEFAULT_FONT


def _estimate_word_timings(
    text: str, duration_us: int,
) -> tuple[list[str], list[int], list[int]]:
    """Per-word start/end times from a caption duration, weighted by word
    length so longer words take proportionally more time.

    Returns (words, starts_us, ends_us). Times are relative to segment start.
    """
    words = text.split()
    if not words:
        return [], [], []
    weights = [max(1, len(w)) + 1 for w in words]  # +1 = inter-word breath
    total = sum(weights)
    starts: list[int] = []
    ends: list[int] = []
    cursor = 0
    for i, w_weight in enumerate(weights):
        share = int(duration_us * w_weight / total)
        starts.append(cursor)
        if i == len(weights) - 1:
            cursor = duration_us
        else:
            cursor += share
        ends.append(cursor)
    return words, starts, ends


def _make_sticker_animation() -> dict[str, Any]:
    """Auxiliary material every text segment must reference."""
    return {
        "id": _uuid(),
        "type": "sticker_animation",
        "animations": [],
        "multi_language_current": "none",
    }


def _make_text_material(
    text: str, font_size: float, color_hex: str, alpha: float,
    *,
    font_path: str | None = None,
    border_color_hex: str | None = None,
    border_width: float = 0.08,
    border_alpha: float = 1.0,
    has_shadow: bool = False,
    shadow_color_hex: str = "#000000",
    shadow_alpha: float = 0.9,
    shadow_distance: float = 5.0,
    background_color_hex: str | None = None,
    background_alpha: float = 0.9,
    highlight_color_hex: str | None = None,
    segment_duration_us: int | None = None,
    line_max_width: float = 0.82,
    highlight_range: tuple[int, int] | None = None,
    highlight_box_color_hex: str | None = None,
    highlight_box_width: float = 0.45,
    highlight_box_alpha: float = 1.0,
) -> dict[str, Any]:
    r, g, b = _hex_to_rgb01(color_hex)
    font = font_path or _CAPCUT_DEFAULT_FONT

    style: dict[str, Any] = {
        "fill": {
            "alpha": float(alpha),
            "content": {
                "render_type": "solid",
                "solid": {"alpha": float(alpha), "color": [r, g, b]},
            },
        },
        "font": {"id": "", "path": font},
        "range": [0, len(text)],
        "size": float(font_size),
    }
    def _apply_stroke(s: dict[str, Any]) -> dict[str, Any]:
        if border_color_hex is not None:
            br, bg, bb = _hex_to_rgb01(border_color_hex)
            s["strokes"] = [{
                "alpha": float(border_alpha),
                "content": {
                    "render_type": "solid",
                    "solid": {"alpha": float(border_alpha), "color": [br, bg, bb]},
                },
                "width": float(border_width),
            }]
        return s

    style = _apply_stroke(style)

    # Multi-style content for per-word highlight: split the styles array
    # into 1-3 entries (before / highlighted-range / after).
    # The highlighted range can have:
    #   - a different fill (highlight_color_hex)              → color change
    #   - a different stroke (highlight_box_color_hex/width)  → "box" via halo
    if highlight_range is not None and highlight_color_hex:
        rs_idx, re_idx = highlight_range
        text_len = len(text)
        rs_idx = max(0, min(rs_idx, text_len))
        re_idx = max(rs_idx, min(re_idx, text_len))

        def _fill(c_hex: str) -> dict[str, Any]:
            cr, cg, cb = _hex_to_rgb01(c_hex)
            return {
                "alpha": float(alpha),
                "content": {
                    "render_type": "solid",
                    "solid": {"alpha": float(alpha), "color": [cr, cg, cb]},
                },
            }

        def _base_stroke() -> list[dict[str, Any]] | None:
            if border_color_hex is None:
                return None
            br, bg, bb = _hex_to_rgb01(border_color_hex)
            return [{
                "alpha": float(border_alpha),
                "content": {
                    "render_type": "solid",
                    "solid": {"alpha": float(border_alpha), "color": [br, bg, bb]},
                },
                "width": float(border_width),
            }]

        def _box_stroke() -> list[dict[str, Any]]:
            assert highlight_box_color_hex is not None
            hr, hg, hb = _hex_to_rgb01(highlight_box_color_hex)
            return [{
                "alpha": float(highlight_box_alpha),
                "content": {
                    "render_type": "solid",
                    "solid": {"alpha": float(highlight_box_alpha),
                              "color": [hr, hg, hb]},
                },
                "width": float(highlight_box_width),
            }]

        def _base_style(rng: tuple[int, int], col: str) -> dict[str, Any]:
            s: dict[str, Any] = {
                "fill": _fill(col),
                "font": {"id": "", "path": font},
                "range": [rng[0], rng[1]],
                "size": float(font_size),
            }
            bs = _base_stroke()
            if bs is not None:
                s["strokes"] = bs
            return s

        def _hl_style(rng: tuple[int, int]) -> dict[str, Any]:
            s: dict[str, Any] = {
                "fill": _fill(highlight_color_hex),
                "font": {"id": "", "path": font},
                "range": [rng[0], rng[1]],
                "size": float(font_size),
            }
            if highlight_box_color_hex is not None:
                s["strokes"] = _box_stroke()
            else:
                bs = _base_stroke()
                if bs is not None:
                    s["strokes"] = bs
            return s

        styles_list: list[dict[str, Any]] = []
        if rs_idx > 0:
            styles_list.append(_base_style((0, rs_idx), color_hex))
        styles_list.append(_hl_style((rs_idx, re_idx)))
        if re_idx < text_len:
            styles_list.append(_base_style((re_idx, text_len), color_hex))
        content = json.dumps({"styles": styles_list, "text": text},
                             separators=(",", ":"))
    else:
        content = json.dumps({"styles": [style], "text": text},
                             separators=(",", ":"))

    # words/ktv_color/is_words_linear have no observed renderer effect on
    # current CapCut; we leave them empty/false. Per-word highlight is
    # achieved via multi-segment + multi-style content above.
    words_data = {"text": [], "start_time": [], "end_time": []}
    return {
        "add_type": 0,
        "alignment": 1,
        "background_alpha": float(background_alpha) if background_color_hex else 1.0,
        "background_color": background_color_hex or "",
        "background_fill": "",
        "background_height": 0.14,
        "background_horizontal_offset": 0.0,
        "background_round_radius": 0.08 if background_color_hex else 0.0,
        "background_style": 1 if background_color_hex else 0,
        "background_vertical_offset": 0.0,
        "background_width": 0.14,
        "base_content": "",
        "bold_width": 0.0,
        "border_alpha": float(border_alpha) if border_color_hex else 1.0,
        "border_color": border_color_hex or "",
        "border_mode": 0,
        "border_width": float(border_width) if border_color_hex else 0.08,
        "caption_template_info": {
            "category_id": "", "category_name": "", "effect_id": "",
            "is_new": False, "path": "", "request_id": "",
            "resource_id": "", "resource_name": "",
            "source_platform": 0, "third_resource_id": "",
        },
        "check_flag": 7,
        "combo_info": {"text_templates": []},
        "content": content,
        "current_words": {"end_time": [], "start_time": [], "text": []},
        "cutoff_postfix": "",
        "enable_path_typesetting": False,
        "fixed_height": -1.0,
        "fixed_width": -1.0,
        "font_category_id": "", "font_category_name": "",
        "font_id": "", "font_name": "",
        "font_path": font,
        "font_resource_id": "",
        "font_size": float(font_size),
        "font_source_platform": 0,
        "font_team_id": "",
        "font_third_resource_id": "",
        "font_title": "none",
        "font_url": "",
        "fonts": [],
        "force_apply_line_max_width": False,
        "global_alpha": float(alpha),
        "group_id": "",
        "has_shadow": bool(has_shadow),
        "id": _uuid(),
        "initial_scale": 1.0,
        "inner_padding": -1.0,
        "is_batch_replace": False,
        "is_lyric_effect": False,
        "is_rich_text": False,
        "is_words_linear": False,
        "italic_degree": 0,
        "ktv_color": "",
        "language": "",
        "layer_weight": 1,
        "letter_spacing": 0.0,
        "line_feed": 1,
        "line_max_width": float(line_max_width),
        "line_spacing": 0.02,
        "lyric_group_id": "",
        "lyrics_template": {
            "category_id": "", "category_name": "", "effect_id": "",
            "panel": "", "path": "", "request_id": "",
            "resource_id": "", "resource_name": "",
        },
        "multi_language_current": "none",
        "name": "",
        "offset_on_path": 0.0,
        "oneline_cutoff": False,
        "operation_type": 0,
        "original_size": [],
        "preset_category": "", "preset_category_id": "",
        "preset_has_set_alignment": False,
        "preset_id": "", "preset_index": 0, "preset_name": "",
        "punc_model": "",
        "recognize_model": "",
        "recognize_task_id": "",
        "recognize_text": "",
        "recognize_type": 0,
        "relevance_segment": [],
        "shadow_alpha": float(shadow_alpha),
        "shadow_angle": -45.0,
        "shadow_color": shadow_color_hex if has_shadow else "",
        "shadow_distance": float(shadow_distance),
        "shadow_point": {"x": 0.6363961030678928, "y": -0.6363961030678927},
        "shadow_smoothing": 0.45,
        "shadow_thickness_projection_angle": 0.0,
        "shadow_thickness_projection_distance": 0.0,
        "shadow_thickness_projection_enable": False,
        "shape_clip_x": False, "shape_clip_y": False,
        "single_char_bg_alpha": 1.0,
        "single_char_bg_color": "",
        "single_char_bg_enable": False,
        "single_char_bg_height": 0.0,
        "single_char_bg_horizontal_offset": 0.0,
        "single_char_bg_round_radius": 0.3,
        "single_char_bg_vertical_offset": 0.0,
        "single_char_bg_width": 0.0,
        "source_from": "",
        "ssml_content": "",
        "style_name": "",
        "sub_template_id": -1,
        "sub_type": 0,
        "subtitle_keywords": None,
        "subtitle_keywords_config": None,
        "subtitle_template_original_fontsize": 0.0,
        "text_alpha": 1.0,
        "text_color": color_hex,
        "text_curve": None,
        "text_exceeds_path_process_type": 0,
        "text_loop_on_path": False,
        "text_preset_resource_id": "",
        "text_size": int(font_size * 2),
        "text_to_audio_ids": [],
        "text_typesetting_path_index": 0,
        "text_typesetting_paths": None,
        "text_typesetting_paths_file": "",
        "translate_original_text": "",
        "tts_auto_update": False,
        "type": "text",
        "typesetting": 0,
        "underline": False,
        "underline_offset": 0.22,
        "underline_width": 0.05,
        "use_effect_default_color": True,
        "words": words_data,
    }


def _text_segment(
    *,
    material_id: str,
    target_start_us: int,
    target_dur_us: int,
    track_render_index: int,
    extra_refs: list[str],
    transform: dict[str, Any],
) -> dict[str, Any]:
    return {
        "caption_info": None, "cartoon": False,
        "clip": transform,
        "color_correct_alg_result": "",
        "common_keyframes": [], "desc": "",
        "digital_human_template_group_id": "",
        "enable_adjust": False, "enable_adjust_mask": False,
        "enable_color_adjust_pro": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False, "enable_hsl_curves": True,
        "enable_lut": False,
        "enable_mask_shadow": False, "enable_mask_stroke": False,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": extra_refs,
        "group_id": "",
        "hdr_settings": None,
        "id": _uuid(),
        "intensifies_audio": False,
        "is_loop": False, "is_placeholder": False, "is_tone_modify": False,
        "keyframe_refs": [], "last_nonzero_volume": 1.0,
        "lyric_keyframes": None,
        "material_id": material_id,
        "raw_segment_id": "",
        "render_index": 14000,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0,
        },
        "reverse": False, "source": "segmentsourcenormal",
        "source_timerange": None,
        "speed": 1.0, "state": 0,
        "target_timerange": {"duration": target_dur_us, "start": target_start_us},
        "template_id": "", "template_scene": "default",
        "track_attribute": 0, "track_render_index": track_render_index,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True, "volume": 1.0,
    }


def add_text(
    name: str,
    text: str,
    duration_seconds: float,
    start_seconds: float = 0.0,
    font_size: float = 15.0,
    color_hex: str = "#FFFFFF",
    alpha: float = 1.0,
    x: float = 0.0,
    y: float = 0.0,
    scale: float = 1.0,
    rotation: float = 0.0,
    track_index: int = 0,
    *,
    language: str | None = None,
    font_path: str | None = None,
    border_color_hex: str | None = None,
    border_width: float = 0.08,
    border_alpha: float = 1.0,
    has_shadow: bool = False,
    shadow_color_hex: str = "#000000",
    shadow_alpha: float = 0.9,
    shadow_distance: float = 5.0,
    background_color_hex: str | None = None,
    background_alpha: float = 0.9,
    highlight_color_hex: str | None = None,
    line_max_width: float = 0.82,
    bold: bool = False,
    highlight_range: tuple[int, int] | None = None,
    highlight_box_color_hex: str | None = None,
    highlight_box_width: float = 0.45,
    highlight_box_alpha: float = 1.0,
) -> dict[str, Any]:
    """Add a text overlay on a text track.

    Font: `language` picks a CapCut system font (en/ar/ja/ko/zh/zh-hant/th/he/bn);
    `font_path` overrides both. Auto-detected from script if neither given.
    `bold=True` upgrades Latin to CapCutSansText-Bold.

    Caption look: `border_color_hex="#000000"` + `has_shadow=True`.

    Per-range highlight: pass `highlight_range=(start_char, end_char)` plus
    `highlight_color_hex` to render that character range in a different
    color. (Used internally by add_captions_from_srt for the karaoke style.)

    `line_max_width` (0..1) — lower wraps text sooner.
    """
    folder, info, meta = _load(name)

    if font_path is None:
        if language:
            font_path = _FONTS_BY_LANG.get(language)
        else:
            font_path = _detect_font_for(text, bold=bold)

    duration_us = int(duration_seconds * US_PER_S)
    mat = _make_text_material(
        text=text, font_size=font_size, color_hex=color_hex, alpha=alpha,
        font_path=font_path,
        border_color_hex=border_color_hex,
        border_width=border_width, border_alpha=border_alpha,
        has_shadow=has_shadow, shadow_color_hex=shadow_color_hex,
        shadow_alpha=shadow_alpha, shadow_distance=shadow_distance,
        background_color_hex=background_color_hex,
        background_alpha=background_alpha,
        highlight_color_hex=highlight_color_hex,
        segment_duration_us=duration_us,
        line_max_width=line_max_width,
        highlight_range=highlight_range,
        highlight_box_color_hex=highlight_box_color_hex,
        highlight_box_width=highlight_box_width,
        highlight_box_alpha=highlight_box_alpha,
    )
    info["materials"]["texts"].append(mat)

    sticker_anim = _make_sticker_animation()
    info["materials"]["material_animations"].append(sticker_anim)

    track = _get_or_create_track(info, "text", track_index)
    target_start = int(start_seconds * US_PER_S)
    target_dur = int(duration_seconds * US_PER_S)

    transform = {
        "alpha": float(alpha),
        "flip": {"horizontal": False, "vertical": False},
        "rotation": float(rotation),
        "scale": {"x": float(scale), "y": float(scale)},
        "transform": {"x": float(x), "y": float(y)},
    }
    seg = _text_segment(
        material_id=mat["id"],
        target_start_us=target_start,
        target_dur_us=target_dur,
        track_render_index=_track_render_index(info, track),
        extra_refs=[sticker_anim["id"]],
        transform=transform,
    )
    track["segments"].append(seg)

    _save(folder, info, meta)
    return {
        "material_id": mat["id"],
        "segment_id": seg["id"],
        "track_index": track_index,
        "start_seconds": target_start / US_PER_S,
        "duration_seconds": target_dur / US_PER_S,
    }


# ---- captions / SRT --------------------------------------------------------

_SRT_TS = re.compile(
    r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)"
)
_TURBOSCRIBE = re.compile(r"^\(Transcribed by TurboScribe\.[^)]*\)\s*", re.IGNORECASE)


def _parse_srt(srt_path: str) -> Iterator[tuple[int, int, str]]:
    """Yield (start_us, end_us, text) for each block."""
    raw = Path(srt_path).expanduser().read_text(encoding="utf-8")
    raw = raw.lstrip("﻿")
    for block in re.split(r"\n\s*\n", raw.strip()):
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        ts_line = lines[1] if lines[0].strip().isdigit() else lines[0]
        text_lines = lines[2:] if lines[0].strip().isdigit() else lines[1:]
        m = _SRT_TS.search(ts_line)
        if not m:
            continue
        h1, mn1, s1, ms1, h2, mn2, s2, ms2 = (int(x) for x in m.groups())
        ms1 = int(str(ms1).ljust(3, "0")[:3])
        ms2 = int(str(ms2).ljust(3, "0")[:3])
        start_us = ((h1 * 3600 + mn1 * 60 + s1) * 1000 + ms1) * 1000
        end_us = ((h2 * 3600 + mn2 * 60 + s2) * 1000 + ms2) * 1000
        text = "\n".join(text_lines).strip()
        text = _TURBOSCRIBE.sub("", text).strip()
        if text:
            yield start_us, end_us, text


CAPTION_STYLE_PRESETS: dict[str, dict[str, Any]] = {
    # Bold white, thick black outline, drop shadow — the "YouTube" look.
    "youtube": {
        "color_hex": "#FFFFFF",
        "border_color_hex": "#000000",
        "border_width": 0.12,
        "has_shadow": True,
        "shadow_distance": 5.0,
        "shadow_alpha": 0.85,
        "bold": True,
    },
    # White on translucent dark pill — clean subtitle look.
    "subtitle": {
        "color_hex": "#FFFFFF",
        "background_color_hex": "#000000",
        "background_alpha": 0.55,
        "has_shadow": False,
        "bold": True,
    },
    # Bold yellow, black outline, shadow — TikTok / shorts.
    "tiktok": {
        "color_hex": "#FFE100",
        "border_color_hex": "#000000",
        "border_width": 0.15,
        "has_shadow": True,
        "shadow_distance": 5.0,
        "bold": True,
    },
    # Plain white, light shadow only — no outline.
    "minimal": {
        "color_hex": "#FFFFFF",
        "has_shadow": True,
        "shadow_distance": 4.0,
        "shadow_alpha": 0.6,
        "bold": True,
    },
    # White base + per-word yellow highlight synced to caption duration.
    # Each word generates its own segment showing the full caption with
    # that word in highlight_color_hex via per-range fill.
    "karaoke": {
        "color_hex": "#FFFFFF",
        "border_color_hex": "#000000",
        "border_width": 0.12,
        "has_shadow": True,
        "shadow_distance": 5.0,
        "highlight_color_hex": "#FFE100",
        "bold": True,
    },
    # Full caption visible. Currently-spoken word stays white but gets a
    # thick yellow stroke that reads as a yellow highlight box behind it.
    "karaoke_box": {
        "color_hex": "#FFFFFF",
        "border_color_hex": "#000000",
        "border_width": 0.10,
        "has_shadow": True,
        "shadow_distance": 5.0,
        "shadow_alpha": 0.7,
        "highlight_color_hex": "#FFFFFF",          # word text stays white
        "highlight_box_color_hex": "#FFE100",      # yellow halo = "box"
        "highlight_box_width": 0.50,
        "bold": True,
    },
    # One word at a time displayed alone in a yellow pill with white text.
    # Use this for shorts/reels where each word flashes in the center.
    "wordbox": {
        "color_hex": "#FFFFFF",
        "background_color_hex": "#FFE100",
        "background_alpha": 1.0,
        "border_color_hex": "#000000",
        "border_width": 0.08,
        "has_shadow": True,
        "shadow_distance": 4.0,
        "shadow_alpha": 0.5,
        "bold": True,
    },
}


def add_captions_from_srt(
    name: str,
    srt_path: str,
    style: str = "youtube",
    time_offset_seconds: float = 0.0,
    max_captions: int | None = None,
    font_size: float = 13.0,
    y: float = 0.42,
    x: float = 0.0,
    scale: float = 1.0,
    track_index: int = 0,
    language: str | None = None,
    line_max_width: float = 0.72,
) -> dict[str, Any]:
    """Parse an SRT file and add styled text segments to the timeline.

    Static styles (one segment per SRT block):
        youtube, subtitle, tiktok, minimal

    Per-word animated styles (N segments per SRT block, one per word):
        karaoke      — full caption visible, current word's fill turns yellow
        karaoke_box  — full caption visible, current word stays white but
                       gets a thick yellow stroke that reads as a highlight
                       box behind it
        wordbox      — single-word display; each spoken word in a yellow pill

    Font is auto-detected from text script (Arabic/CJK/Hebrew/Latin).
    Defaults are tuned for 1920×1080 lower-third placement; pass `y` lower
    (e.g. 0.30) for portrait canvases.
    """
    # Validation up front so errors reach the caller before disk writes.
    if style not in CAPTION_STYLE_PRESETS:
        raise DraftError(
            f"unknown style: {style}. Valid: {sorted(CAPTION_STYLE_PRESETS)}"
        )
    if not Path(srt_path).expanduser().exists():
        raise DraftError(f"SRT file not found: {srt_path}")
    if font_size <= 0:
        raise DraftError(f"font_size must be > 0, got {font_size}")
    if not (-2.0 <= y <= 2.0):
        raise DraftError(f"y should be in [-2.0, 2.0] (canvas-normalized), got {y}")
    if not (0.0 < line_max_width <= 1.0):
        raise DraftError(f"line_max_width must be in (0, 1], got {line_max_width}")
    if max_captions is not None and max_captions <= 0:
        raise DraftError(f"max_captions must be positive, got {max_captions}")
    if language is not None and language not in _FONTS_BY_LANG:
        raise DraftError(
            f"unknown language: {language}. Valid: {sorted(_FONTS_BY_LANG)}"
        )

    preset = dict(CAPTION_STYLE_PRESETS[style])

    captions = list(_parse_srt(srt_path))
    if max_captions is not None:
        captions = captions[:max_captions]
    if not captions:
        raise DraftError(f"no captions parsed from {srt_path}")

    use_bold = bool(preset.pop("bold", False))
    detected_font = (
        _FONTS_BY_LANG.get(language) if language
        else _detect_font_for(captions[0][2], bold=use_bold)
    )

    offset_us = int(time_offset_seconds * US_PER_S)
    added: list[str] = []

    def _per_word_durations(text_len_chars: list[int], total_dur_us: int) -> list[int]:
        """Distribute a caption's duration across its words, weighted by
        char-count + 1 (breath room). Last word absorbs rounding."""
        weights = [max(1, n) + 1 for n in text_len_chars]
        tot = sum(weights)
        out: list[int] = []
        cum = 0
        for i, ww in enumerate(weights):
            if i == len(weights) - 1:
                out.append(total_dur_us - cum)
            else:
                share = int(total_dur_us * ww / tot)
                out.append(share)
                cum += share
        return out

    if style == "wordbox":
        # Per-word display: each spoken word becomes its own segment with
        # the yellow background pill + white text from the preset.
        for start_us, end_us, text in captions:
            target_start_s = (start_us + offset_us) / US_PER_S
            target_dur_s = (end_us - start_us) / US_PER_S
            if target_dur_s <= 0:
                continue
            words = text.split()
            if not words:
                continue
            target_dur_us = int(target_dur_s * US_PER_S)
            durations_us = _per_word_durations([len(w) for w in words], target_dur_us)
            cursor_s = target_start_s
            for word, dur_us in zip(words, durations_us):
                if dur_us <= 0:
                    continue
                result = add_text(
                    name=name, text=word,
                    duration_seconds=dur_us / US_PER_S,
                    start_seconds=cursor_s,
                    font_size=font_size,
                    x=x, y=y, scale=scale,
                    track_index=track_index,
                    font_path=detected_font,
                    line_max_width=line_max_width,
                    **preset,
                )
                added.append(result["segment_id"])
                cursor_s += dur_us / US_PER_S
    elif style in ("karaoke", "karaoke_box"):
        # Full-caption multi-segment: per word, render the full caption
        # with one word's character range styled differently.
        # `karaoke`     -> highlight word's fill changes (color highlight)
        # `karaoke_box` -> highlight word's stroke is thick yellow (box halo)
        highlight_color = preset.pop("highlight_color_hex", "#FFE100")
        highlight_box_color = preset.pop("highlight_box_color_hex", None)
        highlight_box_w = preset.pop("highlight_box_width", 0.45)
        for start_us, end_us, text in captions:
            target_start_s = (start_us + offset_us) / US_PER_S
            target_dur_s = (end_us - start_us) / US_PER_S
            if target_dur_s <= 0:
                continue
            words = text.split()
            if not words:
                continue
            canonical = " ".join(words)
            ranges: list[tuple[int, int]] = []
            cursor = 0
            for w in words:
                ranges.append((cursor, cursor + len(w)))
                cursor += len(w) + 1
            target_dur_us = int(target_dur_s * US_PER_S)
            durations_us = _per_word_durations([len(w) for w in words], target_dur_us)
            cursor_s = target_start_s
            for word_range, dur_us in zip(ranges, durations_us):
                if dur_us <= 0:
                    continue
                result = add_text(
                    name=name, text=canonical,
                    duration_seconds=dur_us / US_PER_S,
                    start_seconds=cursor_s,
                    font_size=font_size,
                    x=x, y=y, scale=scale,
                    track_index=track_index,
                    font_path=detected_font,
                    line_max_width=line_max_width,
                    highlight_range=word_range,
                    highlight_color_hex=highlight_color,
                    highlight_box_color_hex=highlight_box_color,
                    highlight_box_width=highlight_box_w,
                    **preset,
                )
                added.append(result["segment_id"])
                cursor_s += dur_us / US_PER_S
    else:
        for start_us, end_us, text in captions:
            target_start_s = (start_us + offset_us) / US_PER_S
            target_dur_s = (end_us - start_us) / US_PER_S
            if target_dur_s <= 0:
                continue
            result = add_text(
                name=name, text=text,
                duration_seconds=target_dur_s,
                start_seconds=target_start_s,
                font_size=font_size,
                x=x, y=y, scale=scale,
                track_index=track_index,
                font_path=detected_font,
                line_max_width=line_max_width,
                **preset,
            )
            added.append(result["segment_id"])

    return {
        "captions_added": len(added),
        "first_segment": added[0] if added else None,
        "last_segment": added[-1] if added else None,
        "style": style,
        "font_path": detected_font,
        "first_start_seconds": captions[0][0] / US_PER_S + time_offset_seconds,
        "last_end_seconds": captions[-1][1] / US_PER_S + time_offset_seconds,
    }
