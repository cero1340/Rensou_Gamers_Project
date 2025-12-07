obs = obslua

-- === 設定項目 ===
local media_source_name = "AI回答_音声"
local text_source_name = "AI_Thinking_Text"
local mic_source_name = "" 
local filter_name = "LocalVocal" 
local ai_open_source = "" 
local ai_closed_source = ""

-- 正解動画用の設定
local video_source_name = ""       -- OBS上の動画ソース名
local video_trigger_file = ""      -- 監視するトリガーファイルパス

local path_file_path = ""
local thinking_state_file = ""
local yup_sound_path = ""
local last_path = ""
local last_thinking = ""
local last_video_trigger = ""

local hotkey_id = obs.OBS_INVALID_HOTKEY_ID
local connected_source_name = ""
local connected_video_source_name = ""

function script_description()
    return "【Ver 2.2】AIシステム統合版：シーン切替時の自動再生防止対応"
end

function script_properties()
    local props = obs.obs_properties_create()
    obs.obs_properties_add_path(props, "path_file_path", "WAVパス監視ファイル", obs.OBS_PATH_FILE, nil, nil)
    obs.obs_properties_add_path(props, "thinking_state_file", "思考状態監視ファイル", obs.OBS_PATH_FILE, nil, nil)
    obs.obs_properties_add_path(props, "video_trigger_file", "★動画トリガーファイル (video_trigger.txt)", obs.OBS_PATH_FILE, nil, nil)
    
    obs.obs_properties_add_path(props, "yup_sound_path", "相槌音声 (Yup.wav)", obs.OBS_PATH_FILE, nil, nil)
    
    local p_mic = obs.obs_properties_add_list(props, "mic_source_name", "マイクのソース名", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_mic)
    
    obs.obs_properties_add_text(props, "filter_name", "制御するフィルタ名", obs.OBS_TEXT_DEFAULT)

    local p_ai_closed = obs.obs_properties_add_list(props, "ai_closed_source", "AI: 閉じた口の画像", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_ai_closed)
    
    local p_ai_open = obs.obs_properties_add_list(props, "ai_open_source", "AI: 開いた口の画像", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_ai_open)

    -- 動画ソース選択
    local p_video = obs.obs_properties_add_list(props, "video_source_name", "★正解動画(MP4)のソース", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    populate_source_list(p_video)

    return props
end

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
    video_trigger_file = obs.obs_data_get_string(settings, "video_trigger_file")
    yup_sound_path = obs.obs_data_get_string(settings, "yup_sound_path")
    mic_source_name = obs.obs_data_get_string(settings, "mic_source_name")
    filter_name = obs.obs_data_get_string(settings, "filter_name")
    
    ai_open_source = obs.obs_data_get_string(settings, "ai_open_source")
    ai_closed_source = obs.obs_data_get_string(settings, "ai_closed_source")
    video_source_name = obs.obs_data_get_string(settings, "video_source_name")
end

-- フィルタ制御
function set_filter_visibility(source_name, filter_name, visible)
    local source = obs.obs_get_source_by_name(source_name)
    if source then
        local filter = obs.obs_source_get_filter_by_name(source, filter_name)
        if filter then
            obs.obs_source_set_enabled(filter, visible)
            obs.obs_source_release(filter)
        end
        obs.obs_source_release(source)
    end
end

-- ソース表示制御
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

-- WAV再生関数
function play_audio_file(filepath)
    local source = obs.obs_get_source_by_name(media_source_name)
    if source then
        local settings = obs.obs_source_get_settings(source)
        obs.obs_data_set_string(settings, "local_file", filepath)
        obs.obs_data_set_bool(settings, "close_when_inactive", false) 
        
        -- ★修正: シーン切り替え等のアクティブ化で勝手に再生しないようにする
        obs.obs_data_set_bool(settings, "restart_on_activate", false) 
        
        obs.obs_source_update(source, settings)
        obs.obs_source_media_restart(source) -- ここで明示的に再生するので音は鳴ります
        obs.obs_source_release(source)
        obs.obs_data_release(settings)
        obs.script_log(obs.LOG_INFO, "音声再生: " .. filepath)
    end
end

-- 動画再生関数
function play_video_source()
    local source = obs.obs_get_source_by_name(video_source_name)
    if source then
        obs.script_log(obs.LOG_INFO, "★動画再生開始: " .. video_source_name)
        set_source_visibility(video_source_name, true)
        obs.obs_source_media_restart(source)
        obs.obs_source_release(source)
    end
end

-- 再生終了検知 (音声と動画の両方を処理)
function on_media_ended(calldata)
    local source = obs.calldata_source(calldata, "source")
    if source then
        local name = obs.obs_source_get_name(source)
        
        -- A. 音声ソースの場合
        if name == media_source_name then
            local settings = obs.obs_source_get_settings(source)
            local current_file = obs.obs_data_get_string(settings, "local_file")
            obs.obs_data_release(settings)
            
            if current_file ~= yup_sound_path and yup_sound_path ~= "" then
                if mic_source_name ~= "" then
                    set_filter_visibility(mic_source_name, filter_name, false)
                end
            end

        -- B. 動画ソースの場合
        elseif name == video_source_name then
            obs.script_log(obs.LOG_INFO, "★動画終了検知: 非表示にします")
            set_source_visibility(video_source_name, false)
        end
    end
end

-- F9ホットキー
function on_hotkey_pressed(pressed)
    if not pressed then return end
    last_path = ""
    if yup_sound_path ~= "" then play_audio_file(yup_sound_path) end
    if mic_source_name ~= "" then set_filter_visibility(mic_source_name, filter_name, true) end
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
    -- 1. WAV再生監視
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

    -- 2. 思考中テキスト監視
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

    -- 3. 動画トリガー監視
    if video_trigger_file ~= "" then
        local file = io.open(video_trigger_file, "r")
        if file then
            local trigger = file:read("*l")
            io.close(file)
            if trigger and trigger ~= last_video_trigger then
                last_video_trigger = trigger
                if trigger == "1" then
                    play_video_source()
                end
            end
        end
    end

    -- 4. イベントハンドラ接続 (音声ソース)
    local source = obs.obs_get_source_by_name(media_source_name)
    if source then
        local name = obs.obs_source_get_name(source)
        if name ~= connected_source_name then
            local handler = obs.obs_source_get_signal_handler(source)
            obs.signal_handler_connect(handler, "media_ended", on_media_ended)
            connected_source_name = name
        end
        obs.obs_source_release(source)
    else
        connected_source_name = ""
    end

    -- 5. イベントハンドラ接続 (動画ソース)
    if video_source_name ~= "" then
        local v_source = obs.obs_get_source_by_name(video_source_name)
        if v_source then
            local v_name = obs.obs_source_get_name(v_source)
            if v_name ~= connected_video_source_name then
                local handler = obs.obs_source_get_signal_handler(v_source)
                obs.signal_handler_connect(handler, "media_ended", on_media_ended)
                connected_video_source_name = v_name
                obs.script_log(obs.LOG_INFO, "動画用シグナル接続: " .. v_name)
            end
            obs.obs_source_release(v_source)
        else
            connected_video_source_name = ""
        end
    end

    -- 6. 口パク制御
    local is_playing = false
    local source = obs.obs_get_source_by_name(media_source_name)
    if source then
        local state = obs.obs_source_media_get_state(source)
        if state == obs.OBS_MEDIA_STATE_PLAYING then is_playing = true end
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