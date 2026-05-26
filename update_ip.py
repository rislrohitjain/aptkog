import socket
import os
import re
import json

def get_local_ip():
    try:
        # Create a dummy socket connection to an external address to determine primary network interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to hostname resolution if offline
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def update_env(ip):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace HOST=... with HOST=<ip>
        if "HOST=" in content:
            new_content = re.sub(r"HOST=[^\r\n]*", f"HOST={ip}", content)
        else:
            new_content = content + f"\nHOST={ip}"
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[IP_HELPER] Updated {env_path} HOST to {ip}")
    else:
        print(f"[IP_HELPER] .env file not found at {env_path}")

def update_postman(ip):
    postman_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "postman", "antigravity_2.0_collection.json")
    if os.path.exists(postman_path):
        try:
            with open(postman_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Helper to update URL nodes in Postman collection
            def update_item_urls(items):
                for item in items:
                    if "request" in item and "url" in item["request"]:
                        url_node = item["request"]["url"]
                        # Update host array
                        url_node["host"] = [ip]
                        # Update raw URL string
                        raw_url = url_node.get("raw", "")
                        # Replace host in raw url (e.g., http://localhost:8000/api/filter or http://127.0.0.1:8000/api/filter)
                        new_raw = re.sub(r"http://[^:/]+(:[0-9]+)?", f"http://{ip}\\1", raw_url)
                        url_node["raw"] = new_raw
                    if "item" in item:
                        update_item_urls(item["item"])
            
            update_item_urls(data.get("item", []))
            
            with open(postman_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[IP_HELPER] Updated Postman Collection at {postman_path} with IP {ip}")
        except Exception as e:
            print(f"[IP_HELPER] Error updating Postman Collection: {e}")
    else:
        print(f"[IP_HELPER] Postman collection not found at {postman_path}")

def main():
    ip = get_local_ip()
    print(f"[IP_HELPER] Detected Current PC IP Address: {ip}")
    update_env(ip)
    update_postman(ip)

if __name__ == "__main__":
    main()
