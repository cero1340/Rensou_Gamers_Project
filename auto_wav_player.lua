obs = obslua

-- === 設定項目 ===
local media_source_name = "AI回答_音声"
local text_source_name = "AI_Thinking_Text"
local mic_source_name = "" 
local filter_name = "LocalVocal" 
local ai_open_source = ""         -- 追加: AIの口が開いている画像
local ai_closed_source = ""       -- 追加: AIの口が閉じている画像

local path_file_path = ""
local thinking_state_file = ""
local yup_sound_path = ""
local last_path = ""
local last_thinking = ""

local hotkey_id = obs.OBS_INVALID_HOTKEY_ID
local connected_source_name = "" -- 現在シグナル接続しているソース名

function script_description()
    return "【Ver 2.0】口パク対応版：設定強制固定 ＆ 画像切り替え制御"
end

function script_properties()
    local props = obs.obs_properties_create()
    obs.obs_properties_add_path(props, "path_file_path", "WAVパス監視ファイル", obs.OBS_PATH_FILE, nil, nil)
    obs.obs_properties_add_path(props, "thinking_state_file", "制御ファイル", obs.OBS_PATH_FILE, nil, nil)
    obs.obs_properties_add_path(props, "yup_sound_path", "相槌音声 (Yup.wav)", obs.OBS_PATH_FILE, nil, nil)
    
    local p_mic = obs.obs_properties_add_list(props, "mic_source_name", "マイクのソース名", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_mic)
    
    obs.obs_properties_add_text(props, "filter_name", "制御するフィルタ名", obs.OBS_TEXT_DEFAULT)

    -- 追加: AIの画像選択
    local p_ai_closed = obs.obs_properties_add_list(props, "ai_closed_source", "AI: 閉じた口の画像", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_ai_closed)
    
    local p_ai_open = obs.obs_properties_add_list(props, "ai_open_source", "AI: 開いた口の画像 (口パク)", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_ai_open)

    return props
end

-- ソース一覧をリストに入れるヘルパー関数
function populate_source_list(property)
    local sources = obs.obs_enum_sources()
    if sources ~= nil then
        for _, source in ipairs(sources) do
            local name = obs.obs_source_get_name(source)
            obs.obs_property_list_add_string(property, name, name)
        end
        obs.source_list_release(sources)
    end
end

function script_update(settings)
    path_file_path = obs.obs_data_get_string(settings, "path_file_path")
    thinking_state_file = obs.obs_data_get_string(settings, "thinking_state_file")
    yup_sound_path = obs.obs_data_get_string(settings, "yup_sound_path")
    mic_source_name = obs.obs_data_get_string(settings, "mic_source_name")
    filter_name = obs.obs_data_get_string(settings, "filter_name")
    
    -- 追加設定の読み込み
    ai_open_source = obs.obs_data_get_string(settings, "ai_open_source")
    ai_closed_source = obs.obs_data_get_string(settings, "ai_closed_source")
end

-- フィルタ制御関数
function set_filter_visibility(source_name, filter_name, visible)
    local source = obs.obs_get_source_by_name(source_name)
    if source then
        local filter = obs.obs_source_get_filter_by_name(source, filter_name)
        if filter then
            obs.obs_source_set_enabled(filter, visible)
            obs.script_log(obs.LOG_INFO, "マイクフィルタ切り替え: " .. (visible and "ON" or "OFF"))
            obs.obs_source_release(filter)
        end
        obs.obs_source_release(source)
    end
end

-- ソース表示制御関数（汎用）
function set_source_visibility(source_name, visible)
    local source = obs.obs_get_source_by_name(source_name)
    if source then
        local current_scene_source = obs.obs_frontend_get_current_scene()
        if current_scene_source then
            local current_scene = obs.obs_scene_from_source(current_scene_source)
            if current_scene then
                local scene_item = obs.obs_scene_find_source(current_scene, source_name)
                if scene_item then
                    obs.obs_sceneitem_set_visible(scene_item, visible)
                end
            end
            obs.obs_source_release(current_scene_source)
        end
        obs.obs_source_release(source)
    end
end

-- 再生関数
function play_audio_file(filepath)
    local source = obs.obs_get_source_by_name(media_source_name)
    if source then
        local settings = obs.obs_source_get_settings(source)
        
        -- ファイルパスを設定
        obs.obs_data_set_string(settings, "local_file", filepath)

        -- 【重要】設定を強制的に上書き固定する
        obs.obs_data_set_bool(settings, "close_when_inactive", false) 
        obs.obs_data_set_bool(settings, "restart_on_activate", true) 

        obs.obs_source_update(source, settings)
        obs.obs_source_media_restart(source)
        
        obs.obs_source_release(source)
        obs.obs_data_release(settings)
        obs.script_log(obs.LOG_INFO, "再生リクエスト: " .. filepath)
    end
end

-- ★重要：再生終了時に呼ばれるイベントハンドラ
function on_media_ended(calldata)
    local source = obs.calldata_source(calldata, "source")
    if source then
        local settings = obs.obs_source_get_settings(source)
        local current_file = obs.obs_data_get_string(settings, "local_file")
        obs.obs_data_release(settings)

        obs.script_log(obs.LOG_INFO, "【イベント検知】再生終了: " .. current_file)

        -- Yup以外ならマイクOFF（回答が終わったので待機状態へ）
        if current_file ~= yup_sound_path and yup_sound_path ~= "" then
            if mic_source_name ~= "" then
                set_filter_visibility(mic_source_name, filter_name, false)
            end
        end
    end
end

-- F9キー処理
function on_hotkey_pressed(pressed)
    if not pressed then return end
    last_path = ""
    -- Yupを再生
    if yup_sound_path ~= "" then
        play_audio_file(yup_sound_path)
    end
    -- マイクをONにして質問待機
    if mic_source_name ~= "" then
        set_filter_visibility(mic_source_name, filter_name, true)
    end
end

function script_load(settings)
    hotkey_id = obs.obs_hotkey_register_frontend("ai_yup_trigger", "【AIシステム】呼びかけ (Yup/起動)", on_hotkey_pressed)
    local data = obs.obs_data_get_array(settings, "ai_yup_trigger")
    obs.obs_hotkey_load(hotkey_id, data)
    obs.obs_data_array_release(data)
end

function script_save(settings)
    local data = obs.obs_hotkey_save(hotkey_id)
    obs.obs_data_set_array(settings, "ai_yup_trigger", data)
    obs.obs_data_array_release(data)
end

function script_tick(seconds)
    -- 1. WAV再生処理
    if path_file_path ~= "" then
        local file = io.open(path_file_path, "r")
        if file then
            local new_path = file:read("*l")
            io.close(file)
            if new_path == nil or new_path == "" then
                last_path = ""
            elseif new_path ~= last_path then
                last_path = new_path
                play_audio_file(new_path)
            end
        end
    end

    -- 2. 文字表示処理
    if thinking_state_file ~= "" then
        local file = io.open(thinking_state_file, "r")
        if file then
            local state = file:read("*l")
            io.close(file)
            if state and state ~= last_thinking then
                last_thinking = state
                if state == "1" then
                    set_source_visibility(text_source_name, true)
                else
                    set_source_visibility(text_source_name, false)
                end
            end
        end
    end

    -- 3. イベントハンドラの接続管理
    local source = obs.obs_get_source_by_name(media_source_name)
    if source then
        local name = obs.obs_source_get_name(source)
        if name ~= connected_source_name then
            local handler = obs.obs_source_get_signal_handler(source)
            obs.signal_handler_connect(handler, "media_ended", on_media_ended)
            connected_source_name = name
            obs.script_log(obs.LOG_INFO, "シグナル接続完了: " .. name)
        end
        obs.obs_source_release(source)
    else
        connected_source_name = ""
    end

    -- 4. 口パク制御 (追加)
    local is_playing = false
    local source = obs.obs_get_source_by_name(media_source_name)
    if source then
        local state = obs.obs_source_media_get_state(source)
        if state == obs.OBS_MEDIA_STATE_PLAYING then
            is_playing = true
        end
        obs.obs_source_release(source)
    end

    if is_playing then
        if ai_open_source ~= "" then set_source_visibility(ai_open_source, true) end
        if ai_closed_source ~= "" then set_source_visibility(ai_closed_source, false) end
    else
        if ai_open_source ~= "" then set_source_visibility(ai_open_source, false) end
        if ai_closed_source ~= "" then set_source_visibility(ai_closed_source, true) end
    end
end