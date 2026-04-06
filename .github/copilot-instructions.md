# Copilot instructions for `bili_capcmdtokb`

## Big picture architecture
- This project is a desktop Tkinter danmaku client with an async network backend.
- Entry points: `run_danmaku.py` (launcher) and `danmaku/app.py` (`DanmakuApp`).
- `DanmakuApp` runs Tkinter on the main thread and an `asyncio` loop on a background thread.
- Cross-thread handoff uses `queue.Queue` in `danmaku/ui/danmaku_window.py` (`danmaku_queue`, `gift_queue`).
- Network layer is in `ws/`: `ws.py` handles WebSocket lifecycle; `danmaku_parser.py` parses binary packets.
- Business state is centralized in `danmaku/core/statistics.py` (`StatisticsManager`) with thread locks.

## Data flow you should preserve
- `BiliStreamClient.connect_to_host()` receives binary WS frames and calls `_parse_ws_message()`.
- `_parse_ws_message()` uses `parse_ws_stream()` + `extract_comment_info()` and enqueues normalized dicts.
- Message shape used by app/UI: `{'type': 'danmaku'|'heartbeat', 'uid', 'nickname', 'text', ...}`.
- `DanmakuApp._consume_danmaku()` reads via `await bsclient.recv_danmaku()` and updates UI queue + stats.
- Heartbeat replies (`cmd == '_HEARTBEAT'`) update online/popularity via `statistics.update_online(...)`.

## Developer workflows (actual project commands)
- Run app: `python run_danmaku.py`
- Alternate run: `python -m danmaku.app`
- Run smoke tests script: `python test_danmaku.py`
- Install package locally: `pip install .`
- Main log output file: `bili_capcmdtokb_info.log` (configured in `log/log.py`).

## Project-specific conventions
- Logging wrapper is required: use `from log.log import logger` then `logger.pr_info/pr_debug/pr_error`.
- Keep normalized message keys (`uid`, `nickname`, `text`, `room_id`) consistent across modules.
- UI updates must stay thread-safe: use `root.after(...)` or enqueue for `_poll_queues()`.
- Stats mutations should go through `StatisticsManager` methods (it owns locking).
- Existing style mixes Chinese comments/text and English identifiers; keep that style consistent.

## Integration points and dependencies
- Bilibili endpoints and websocket auth/signing are in `ws/ws.py` and `ws/key.py` (`_WbiSigner`).
- Compression handling for protocol versions is in `ws/danmaku_parser.py` (Brotli + zlib).
- Keyboard command bridge is `ws/command.py` (`push_next_command`, `fetch_command_list`) and `keyboard` package.
- Optional `blivedm` path exists in `danmaku/core/blivedm_client.py` and `RoomManager.connect_room()` fallback logic.

## When modifying behavior
- Prefer fixing parsing/normalization at `ws/danmaku_parser.py` or `ws/ws.py` before patching UI.
- If adding a new message type, update parser normalization first, then app consume path, then UI/statistics.
- Validate by running `python test_danmaku.py` and a manual connect flow from `run_danmaku.py`.