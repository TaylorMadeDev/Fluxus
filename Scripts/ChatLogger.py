"""
ChatLogger — Log all chat messages to a file with timestamps.
"""
import minescript
import time
from pathlib import Path
from datetime import datetime

# @ui.title "Chat Logger"
# @ui.text log_file "Log File" "chat_log.txt" -- Output file name
# @ui.toggle timestamp "Timestamps" true -- Add timestamps to each message
# @ui.toggle echo_status "Echo Status" true -- Show status in chat
# @ui.dropdown format "Format" plain,csv,json -- Log file format

def main():
    print("=== Chat Logger ===")
    print(f"  Logging to: {log_file}")
    print(f"  Format: {format}")

    log_path = Path(__file__).parent / log_file
    messages_logged = 0

    if format == "csv":
        if not log_path.exists():
            log_path.write_text("timestamp,message\n", encoding="utf-8")
    elif format == "json":
        if not log_path.exists():
            log_path.write_text("[\n", encoding="utf-8")

    def on_chat(msg):
        nonlocal messages_logged
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")

        with open(log_path, "a", encoding="utf-8") as f:
            if format == "plain":
                if timestamp:
                    f.write(f"[{ts}] {msg}\n")
                else:
                    f.write(f"{msg}\n")
            elif format == "csv":
                safe_msg = msg.replace('"', '""')
                f.write(f'"{ts}","{safe_msg}"\n')
            elif format == "json":
                import json
                entry = {"time": ts, "message": msg}
                f.write(f"  {json.dumps(entry)},\n")

        messages_logged += 1
        if echo_status and messages_logged % 50 == 0:
            minescript.echo(f"[ChatLogger] {messages_logged} messages logged")

    try:
        minescript.register_chat_listener(on_chat)
        if echo_status:
            minescript.echo(f"[ChatLogger] Started — logging to {log_file}")
        print(f"Chat listener registered. Logging to {log_path}")

        # Keep alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"Chat logger stopped. {messages_logged} messages logged.")


main()
