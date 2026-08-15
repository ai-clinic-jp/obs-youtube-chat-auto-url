# -*- coding: utf-8 -*-
"""
YouTube Chat Auto URL for OBS Studio

OBSでYouTube配信を開始したとき、
現在選択中のYouTube配信ID（broadcast_id）をOBS内部から取得し、
指定したブラウザソースのURLを自動更新します。

URL:
https://www.youtube.com/live_chat?is_popout=1&v=<VIDEO_ID>

前提:
- OBS StudioでYouTubeアカウント連携を使用している
- 「配信の管理」から配信枠を選択している
- コメント表示用のブラウザソースがある
"""

import obspython as obs


SCRIPT_NAME = "YouTube Chat Auto URL"
DEFAULT_BROWSER_SOURCE = "コメント欄"
CHAT_URL = "https://www.youtube.com/live_chat?is_popout=1&v={}"

browser_source_name = DEFAULT_BROWSER_SOURCE

startup_retry_count = 0
startup_retry_max = 10
startup_retry_interval_ms = 1000
startup_retry_pending = False


def log(message):
    obs.script_log(obs.LOG_INFO, f"[{SCRIPT_NAME}] {message}")


def warn(message):
    obs.script_log(obs.LOG_WARNING, f"[{SCRIPT_NAME}] {message}")


def error(message):
    obs.script_log(obs.LOG_ERROR, f"[{SCRIPT_NAME}] {message}")


def script_description():
    return """
<h2>YouTube Chat Auto URL</h2>
<p>OBSでYouTube配信を開始すると、OBS内部の配信情報からVideo IDを取得し、指定したブラウザソースのYouTubeライブチャットURLを自動更新します。</p>
<p><b>YouTube側からライブ配信を検索しません。</b> OBSが現在選択している配信の <code>broadcast_id</code> を直接利用します。</p>
"""


def script_defaults(settings):
    obs.obs_data_set_default_string(
        settings,
        "browser_source_name",
        DEFAULT_BROWSER_SOURCE,
    )


def script_properties():
    props = obs.obs_properties_create()

    source_list = obs.obs_properties_add_list(
        props,
        "browser_source_name",
        "コメント表示ブラウザソース",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING,
    )

    sources = obs.obs_enum_sources()
    if sources is not None:
        try:
            for source in sources:
                if source is None:
                    continue

                if obs.obs_source_get_id(source) == "browser_source":
                    name = obs.obs_source_get_name(source)
                    if name:
                        obs.obs_property_list_add_string(
                            source_list,
                            name,
                            name,
                        )
        finally:
            obs.source_list_release(sources)

    obs.obs_properties_add_button(
        props,
        "test_update",
        "今すぐURL更新をテスト",
        on_test_update,
    )

    return props


def script_update(settings):
    global browser_source_name

    browser_source_name = (
        obs.obs_data_get_string(settings, "browser_source_name")
        or DEFAULT_BROWSER_SOURCE
    )


def script_load(settings):
    obs.obs_frontend_add_event_callback(on_frontend_event)
    log("スクリプトを読み込みました。")
    log("配信開始時にYouTubeコメント欄URLを自動更新します。")


def script_unload():
    global startup_retry_pending

    startup_retry_pending = False

    try:
        obs.timer_remove(startup_retry_tick)
    except Exception:
        pass

    try:
        obs.obs_frontend_remove_event_callback(on_frontend_event)
    except Exception:
        pass


def on_frontend_event(event):
    global startup_retry_count, startup_retry_pending

    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED:
        log("OBSの配信開始イベントを検知しました。")

        startup_retry_count = 0
        startup_retry_pending = True

        try:
            obs.timer_remove(startup_retry_tick)
        except Exception:
            pass

        # 配信開始直後はOBS内部のbroadcast_id反映前の場合があるため、
        # 1秒おきに最大10回まで取得を試します。
        obs.timer_add(startup_retry_tick, startup_retry_interval_ms)

    elif event == obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED:
        startup_retry_pending = False

        try:
            obs.timer_remove(startup_retry_tick)
        except Exception:
            pass


def startup_retry_tick():
    global startup_retry_count, startup_retry_pending

    if not startup_retry_pending:
        try:
            obs.timer_remove(startup_retry_tick)
        except Exception:
            pass
        return

    startup_retry_count += 1

    video_id = get_broadcast_id()

    if video_id:
        startup_retry_pending = False

        try:
            obs.timer_remove(startup_retry_tick)
        except Exception:
            pass

        log(
            f"Video ID取得成功 "
            f"({startup_retry_count}/{startup_retry_max}): {video_id}"
        )
        update_browser_url(video_id)
        return

    if startup_retry_count >= startup_retry_max:
        startup_retry_pending = False

        try:
            obs.timer_remove(startup_retry_tick)
        except Exception:
            pass

        warn(
            "Video IDを取得できませんでした。"
            "OBSとYouTubeのアカウント連携、および"
            "「配信の管理」で配信枠を選択しているか確認してください。"
        )
        return

    log(
        f"Video ID未取得 "
        f"({startup_retry_count}/{startup_retry_max})。"
        "1秒後に再試行します。"
    )


def get_broadcast_id():
    """OBSが現在保持しているYouTube broadcast_idを取得する。"""
    service = obs.obs_frontend_get_streaming_service()

    if not service:
        return None

    settings = None

    try:
        settings = obs.obs_service_get_settings(service)
        if not settings:
            return None

        broadcast_id = obs.obs_data_get_string(
            settings,
            "broadcast_id",
        ).strip()

        return broadcast_id or None

    except Exception as exc:
        error(
            f"broadcast_id取得中にエラー: "
            f"{type(exc).__name__}: {exc}"
        )
        return None

    finally:
        if settings:
            try:
                obs.obs_data_release(settings)
            except Exception:
                pass


def update_browser_url(video_id):
    """指定したブラウザソースのURLを現在のYouTubeライブチャットへ更新する。"""
    source = obs.obs_get_source_by_name(browser_source_name)

    if not source:
        warn(
            f"ブラウザソース「{browser_source_name}」"
            "が見つかりません。"
        )
        return False

    settings = None

    try:
        if obs.obs_source_get_id(source) != "browser_source":
            warn(
                f"「{browser_source_name}」は"
                "ブラウザソースではありません。"
            )
            return False

        settings = obs.obs_source_get_settings(source)
        new_url = CHAT_URL.format(video_id)

        obs.obs_data_set_string(settings, "url", new_url)
        obs.obs_source_update(source, settings)

        log(
            f"「{browser_source_name}」のURLを更新しました: "
            f"{new_url}"
        )
        return True

    except Exception as exc:
        error(
            f"ブラウザソース更新中にエラー: "
            f"{type(exc).__name__}: {exc}"
        )
        return False

    finally:
        if settings:
            try:
                obs.obs_data_release(settings)
            except Exception:
                pass

        try:
            obs.obs_source_release(source)
        except Exception:
            pass


def on_test_update(props, prop):
    video_id = get_broadcast_id()

    if not video_id:
        warn(
            "Video IDを取得できませんでした。"
            "OBSの「配信の管理」で配信枠を選択してから"
            "再度お試しください。"
        )
        return True

    log(f"テスト: Video ID取得成功: {video_id}")
    update_browser_url(video_id)
    return True
