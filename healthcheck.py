import os
import sys

def main():
    required_files = [
        "app.py",
        "requirements.txt",
        "assets/NotoSans-Regular.ttf",
        "assets/NotoSans-Bold.ttf",
    ]

    missing = [f for f in required_files if not os.path.exists(f)]

    if missing:
        print("Missing files:", ", ".join(missing))
        sys.exit(1)

    print("OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
