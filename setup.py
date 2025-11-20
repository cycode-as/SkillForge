import os

def create_env_file():
    print("--- API KEY SETUP ---")
    key = input("Paste your Google API Key here: ").strip()
    
    if not key.startswith("AIza"):
        print("⚠  Warning: That doesn't look like a standard Google API Key (starts with AIza).")
        confirm = input("Use it anyway? (y/n): ")
        if confirm.lower() != 'y':
            return

    # Write to .env file
    with open(".env", "w") as f:
        f.write(f"GOOGLE_API_KEY={key}")
    
    print("\n✅ SUCCESS! '.env' file created.")
    print("You can now run 'python app.py'")

if __name__ == "__main__":
    create_env_file()