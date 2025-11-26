obs = obslua

-- 設定項目
local media_source_name = "AI回答_音声"
local text_source_name = "AI_Thinking_Text"
local mic_source_name = "" 
local filter_name = "LocalVocal" 

local path_file_path = ""
local thinking_state_file = ""
local last_path = ""
local last_thinking = ""

function script_description()
    return "【完成版】歪み対策(フィルタ制御) ＆ 考え中表示 ＆ WAV再生"
end

function script_properties()
    local props = obs.obs_properties_create()
    
    -- ファイル監視設定
    obs.obs_properties_add_path(props, "path_file_path", "WAVパス監視ファイル (next_wav_path.txt)", obs.OBS_PATH_FILE, nil, nil)
    obs.obs_properties_add_path(props, "thinking_state_file", "制御ファイル (thinking_state.txt)", obs.OBS_PATH_FILE, nil, nil)
    
    -- マイクフィルタ制御設定
    local p_mic = obs.obs_properties_add_list(props, "mic_source_name", "マイクのソース名", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    local sources = obs.obs_enum_sources()
    if sources ~= nil then
        for _, source in ipairs(sources) do
            local name = obs.obs_source_get_name(source)
            obs.obs_property_list_add_string(p_mic, name, name)
        end
        obs.source_list_release(sources)
    end

    obs.obs_properties_add_text(props, "filter_name", "制御するフィルタ名", obs.OBS_TEXT_DEFAULT)

    return props
end

function script_update(settings)
    path_file_path = obs.obs_data_get_string(settings, "path_file_path")
    thinking_state_file = obs.obs_data_get_string(settings, "thinking_state_file")
    mic_source_name = obs.obs_data_get_string(settings, "mic_source_name")
    filter_name = obs.obs_data_get_string(settings, "filter_name")
end

-- フィルタON/OFF関数
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

-- テキストON/OFF関数（エラー修正済み）
function set_text_visibility(source_name, visible)
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
end

function script_tick(seconds)
    -- 1. WAV再生処理
    if path_file_path ~= "" then
        local file = io.open(path_file_path, "r")
        if file then
            local new_path = file:read("*l")
            io.close(file)

            -- ファイルが空ならリセット
            if new_path == nil or new_path == "" then
                last_path = ""
            -- 前回と違うなら再生
            elseif new_path ~= last_path then
                last_path = new_path
                local source = obs.obs_get_source_by_name(media_source_name)
                if source then
                    local settings = obs.obs_source_get_settings(source)
                    obs.obs_data_set_string(settings, "local_file", new_path)
                    obs.obs_source_update(source, settings)
                    obs.obs_source_media_restart(source)
                    obs.obs_source_release(source)
                    obs.obs_data_release(settings)
                end
            end
        end
    end

    -- 2. 状態制御処理（フィルタ ＆ 文字）
    if thinking_state_file ~= "" then
        local file = io.open(thinking_state_file, "r")
        if file then
            local state = file:read("*l")
            io.close(file)
            
            if state and state ~= last_thinking then
                last_thinking = state
                
                if state == "1" then
                    -- 1: 考え中 (文字ON / マイクOFF)
                    set_text_visibility(text_source_name, true)
                    if mic_source_name ~= "" then set_filter_visibility(mic_source_name, filter_name, false) end
                
                elseif state == "2" then
                    -- 2: 一時停止 (文字OFF / マイクOFF)
                    set_text_visibility(text_source_name, false)
                    if mic_source_name ~= "" then set_filter_visibility(mic_source_name, filter_name, false) end
                
                else
                    -- 0: 待機中 (文字OFF / マイクON)
                    set_text_visibility(text_source_name, false)
                    if mic_source_name ~= "" then set_filter_visibility(mic_source_name, filter_name, true) end
                end
            end
        end
    end
end