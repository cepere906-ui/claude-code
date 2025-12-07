# Flask chat UI for configurable Claude API

This example recreates the simple Claude-style chat UI but moves the API endpoint
and API key into persisted application settings.

## Usage

1. Install dependencies:

```bash
pip install flask requests
```

2. Run the app:

```bash
python app.py
```

3. Open http://127.0.0.1:5000 in your browser.

4. Set the API endpoint and key in **Настройки**. They are saved to
`config.json` so you only need to enter them once.

## Notes

- The app streams responses from the configured `/chat/completions` endpoint.
- If `config.json` does not exist it will be created automatically the first
  time settings are saved.
- Leave the API key field empty to keep the currently stored value when
  updating other settings.
