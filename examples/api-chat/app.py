import json
import os
from pathlib import Path
from typing import Dict

import requests
from flask import Flask, Response, jsonify, render_template_string, request

app = Flask(__name__)

CONFIG_PATH = Path(__file__).with_name("config.json")
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.algion.dev/v1",
}


def load_config() -> Dict[str, str]:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            if isinstance(data, dict):
                return {**DEFAULT_CONFIG, **{k: str(v) for k, v in data.items() if v is not None}}
        except Exception:
            # Fall back to defaults if the file is unreadable or invalid
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, str]) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False))


config = load_config()

HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #fff;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            width: 100%;
            border-bottom: 1px solid #eee;
            padding: 14px 20px;
            display: flex;
            justify-content: center;
        }
        .header-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            max-width: 800px;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px 20px 40px 20px;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
        }
        .message {
            margin-bottom: 24px;
            line-height: 1.6;
        }
        .user {
            color: #666;
            font-weight: 500;
            white-space: pre-wrap;
        }
        .assistant {
            color: #000;
        }
        .assistant p { margin: 12px 0; }
        .assistant h1, .assistant h2, .assistant h3 {
            margin: 16px 0 8px 0;
            font-weight: 600;
        }
        .assistant h1 { font-size: 24px; }
        .assistant h2 { font-size: 20px; }
        .assistant h3 { font-size: 18px; }
        .assistant code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
        }
        .assistant pre {
            background: #f5f5f5;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 12px 0;
        }
        .assistant pre code {
            background: none;
            padding: 0;
        }
        .assistant ul, .assistant ol { margin: 12px 0 12px 24px; }
        .assistant li { margin: 6px 0; }
        .assistant strong { font-weight: 600; }
        .assistant em { font-style: italic; }
        .file-badge {
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 13px;
            margin: 4px 0;
            color: #555;
        }
        .input-area {
            border-top: 1px solid #eee;
            padding: 20px;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
        }
        #userInput {
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            font-size: 15px;
            font-family: inherit;
            resize: none;
            outline: none;
            margin-bottom: 8px;
            min-height: 60px;
        }
        #userInput:focus { border-color: #999; }
        .button-row {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        #fileInput { display: none; }
        #fileBtn {
            background: #f5f5f5;
            color: #000;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 14px;
        }
        #fileBtn:hover { background: #e8e8e8; }
        #sendBtn {
            background: #000;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 500;
        }
        #sendBtn:hover:not(:disabled) { background: #333; }
        #sendBtn:disabled { background: #ccc; cursor: not-allowed; }
        #fileName { font-size: 13px; color: #666; }
        .settings {
            background: #f9f9f9;
            border: 1px solid #eee;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .settings h3 { margin: 0 0 12px 0; }
        .settings label { display: block; font-size: 13px; color: #444; margin-bottom: 6px; }
        .settings input {
            width: 100%;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 12px;
            font-size: 14px;
        }
        .settings-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        #saveSettings {
            background: #000;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        #saveSettings:disabled { background: #aaa; cursor: not-allowed; }
        #settingsStatus { font-size: 13px; color: #444; }
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <strong>Claude Code API Chat</strong>
            <button id="toggleSettings" style="border: 1px solid #ddd; padding: 6px 12px; border-radius: 8px; background: #f5f5f5; cursor: pointer;">Настройки</button>
        </div>
    </header>

    <div class="messages" id="messages"></div>

    <div class="input-area">
        <div class="settings" id="settingsPanel" style="display: none;">
            <h3>Параметры API</h3>
            <label for="baseUrl">Endpoint</label>
            <input id="baseUrl" placeholder="https://api.algion.dev/v1" />
            <label for="apiKey">API Key</label>
            <input id="apiKey" type="password" placeholder="Введите ключ или оставьте пустым чтобы не менять" />
            <div class="settings-actions">
                <button id="saveSettings">Сохранить</button>
                <span id="settingsStatus"></span>
            </div>
            <small id="keyState" style="color:#666"></small>
        </div>

        <textarea id="userInput" placeholder="Напишите сообщение..." rows="3"></textarea>
        <div class="button-row">
            <input type="file" id="fileInput" accept=".txt">
            <button id="fileBtn">📎 Файл</button>
            <span id="fileName"></span>
            <button id="sendBtn">Отправить</button>
        </div>
    </div>

    <script>
        const messages = document.getElementById('messages');
        const input = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const fileInput = document.getElementById('fileInput');
        const fileBtn = document.getElementById('fileBtn');
        const fileName = document.getElementById('fileName');
        const toggleSettings = document.getElementById('toggleSettings');
        const settingsPanel = document.getElementById('settingsPanel');
        const baseUrlInput = document.getElementById('baseUrl');
        const apiKeyInput = document.getElementById('apiKey');
        const saveSettingsBtn = document.getElementById('saveSettings');
        const settingsStatus = document.getElementById('settingsStatus');
        const keyState = document.getElementById('keyState');

        let attachedFile = null;
        let hasApiKey = false;

        toggleSettings.addEventListener('click', async () => {
            const isVisible = settingsPanel.style.display === 'block';
            settingsPanel.style.display = isVisible ? 'none' : 'block';
            if (!isVisible) {
                await loadConfig();
            }
        });

        async function loadConfig() {
            try {
                const res = await fetch('/config');
                if (!res.ok) throw new Error('Не удалось получить конфигурацию');
                const data = await res.json();
                baseUrlInput.value = data.base_url || '';
                hasApiKey = !!data.has_api_key;
                keyState.textContent = hasApiKey ? 'API Key сохранён в приложении.' : 'API Key пока не задан.';
                apiKeyInput.value = '';
            } catch (err) {
                settingsStatus.textContent = '⚠️ ' + err.message;
            }
        }

        async function saveConfig() {
            saveSettingsBtn.disabled = true;
            settingsStatus.textContent = 'Сохранение...';
            try {
                const body = {
                    base_url: baseUrlInput.value.trim(),
                };
                if (apiKeyInput.value.trim()) {
                    body.api_key = apiKeyInput.value.trim();
                }
                const res = await fetch('/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Не удалось сохранить');
                settingsStatus.textContent = '✅ Сохранено';
                hasApiKey = data.has_api_key;
                keyState.textContent = hasApiKey ? 'API Key сохранён в приложении.' : 'API Key пока не задан.';
                apiKeyInput.value = '';
            } catch (err) {
                settingsStatus.textContent = '❌ ' + err.message;
            } finally {
                saveSettingsBtn.disabled = false;
            }
        }

        saveSettingsBtn.addEventListener('click', saveConfig);

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function addMessage(role, content, file = null) {
            const div = document.createElement('div');
            div.className = `message ${role}`;

            if (file) {
                const badge = document.createElement('div');
                badge.className = 'file-badge';
                badge.textContent = `📎 ${file}`;
                div.appendChild(badge);
                div.appendChild(document.createElement('br'));
            }

            const contentDiv = document.createElement('div');
            contentDiv.style.whiteSpace = 'pre-wrap';
            contentDiv.textContent = content;
            div.appendChild(contentDiv);

            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return contentDiv;
        }

        fileBtn.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    attachedFile = {
                        name: file.name,
                        content: event.target.result
                    };
                    fileName.textContent = `✓ ${file.name}`;
                };
                reader.readAsText(file);
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 200) + 'px';
        });

        sendBtn.addEventListener('click', sendMessage);

        async function sendMessage() {
            const text = input.value.trim();
            if (!text && !attachedFile) return;

            sendBtn.disabled = true;
            sendBtn.textContent = '...';

            let fullMessage = text;
            let displayFile = null;

            if (attachedFile) {
                displayFile = attachedFile.name;
                fullMessage = `${text}\n\n---\nФайл: ${attachedFile.name}\n---\n${attachedFile.content}`;
            }

            addMessage('user', text || '(пустое сообщение)', displayFile);
            input.value = '';
            input.style.height = 'auto';
            fileName.textContent = '';
            fileInput.value = '';
            attachedFile = null;

            const assistantContent = addMessage('assistant', '');
            let fullText = '';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: fullMessage })
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => null);
                    throw new Error(errData?.error || `HTTP ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6).trim();
                            if (data === '[DONE]') continue;

                            try {
                                const json = JSON.parse(data);

                                if (json.error) {
                                    assistantContent.textContent = '❌ ' + json.error;
                                    break;
                                }

                                const content = json.choices?.[0]?.delta?.content || '';
                                if (content) {
                                    fullText += content;
                                    assistantContent.textContent = fullText;
                                    messages.scrollTop = messages.scrollHeight;
                                }
                            } catch (e) {
                                console.warn('Parse error:', e);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                assistantContent.textContent = '❌ ' + error.message;
            }

            sendBtn.disabled = false;
            sendBtn.textContent = 'Отправить';
        }

        loadConfig();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    response = app.make_response(render_template_string(HTML))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/config", methods=["GET", "POST"])
def config_endpoint():
    global config

    if request.method == "GET":
        return jsonify(
            {
                "base_url": config.get("base_url", DEFAULT_CONFIG["base_url"]),
                "has_api_key": bool(config.get("api_key")),
            }
        )

    payload = request.get_json(force=True) or {}
    base_url = (payload.get("base_url") or "").strip().rstrip("/")
    incoming_key = payload.get("api_key")
    new_config = config.copy()

    if not base_url:
        return jsonify({"error": "Endpoint не может быть пустым"}), 400

    new_config["base_url"] = base_url

    if incoming_key is not None:
        incoming_key = incoming_key.strip()
        if incoming_key:
            new_config["api_key"] = incoming_key
    if not new_config.get("api_key"):
        return jsonify({"error": "API Key обязателен"}), 400

    config = new_config
    save_config(config)

    return jsonify({"ok": True, "has_api_key": bool(config.get("api_key"))})


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    print(f"\n{'=' * 60}")
    print(f"📤 USER: {user_message[:200]}...")
    print(f"{'=' * 60}\n")

    def generate():
        if not config.get("api_key"):
            yield f"data: {json.dumps({'error': 'API Key не задан в настройках'})}\n\n"
            return
        if not config.get("base_url"):
            yield f"data: {json.dumps({'error': 'Endpoint не задан в настройках'})}\n\n"
            return

        try:
            target_url = f"{config['base_url'].rstrip('/')}/chat/completions"
            print(f"🔄 API request to {target_url}")
            response = requests.post(
                target_url,
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-opus-4.5",
                    "messages": [{"role": "user", "content": user_message}],
                    "stream": True
                },
                stream=True,
                timeout=60
            )

            print(f"✅ Status: {response.status_code}")

            if response.status_code != 200:
                error = response.text
                print(f"❌ API Error: {error}")
                yield f"data: {json.dumps({'error': f'{response.status_code}: {error}'})}\n\n"
                return

            count = 0
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    count += 1
                    if count <= 2:
                        print(f"📦 {count}: {decoded[:80]}...")
                    yield decoded + '\n'

            print(f"✅ Done. Chunks: {count}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port, host='127.0.0.1')
