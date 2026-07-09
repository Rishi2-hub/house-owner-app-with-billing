"""
One-time helper: reads a Firebase service-account JSON file and writes a
correctly formatted .streamlit/secrets.toml, avoiding manual copy/paste
mistakes with the private_key field.
"""

import sys
import json
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_secrets.py <path-to-json> <storage-bucket>")
        sys.exit(1)

    json_path = sys.argv[1]
    storage_bucket = sys.argv[2]

    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    required = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url",
    ]
    missing = [k for k in required if k not in d]
    if missing:
        print(f"ERROR: JSON file is missing expected fields: {missing}")
        sys.exit(1)

    universe_domain = d.get("universe_domain", "googleapis.com")

    out_dir = os.path.join(".streamlit")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "secrets.toml")

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("[firebase]\n")
        f.write(f'type = "{d["type"]}"\n')
        f.write(f'project_id = "{d["project_id"]}"\n')
        f.write(f'private_key_id = "{d["private_key_id"]}"\n')
        f.write('private_key = """' + d["private_key"] + '"""\n')
        f.write(f'client_email = "{d["client_email"]}"\n')
        f.write(f'client_id = "{d["client_id"]}"\n')
        f.write(f'auth_uri = "{d["auth_uri"]}"\n')
        f.write(f'token_uri = "{d["token_uri"]}"\n')
        f.write(f'auth_provider_x509_cert_url = "{d["auth_provider_x509_cert_url"]}"\n')
        f.write(f'client_x509_cert_url = "{d["client_x509_cert_url"]}"\n')
        f.write(f'universe_domain = "{universe_domain}"\n')
        f.write(f'storage_bucket = "{storage_bucket}"\n')

    print(f"Wrote {out_path} successfully.")


if __name__ == "__main__":
    main()