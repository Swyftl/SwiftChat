pyinstaller --noconsole --onefile --add-data "resources;resources" --name SwiftChat client.py
pyinstaller server.py --onefile --noconsole