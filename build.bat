pyinstaller --noconsole --onefile --add-data "resources;resources" --name SwiftChat client.py
pyinstaller --onefile --noconsole --name SwiftChatServer server.py