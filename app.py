import subprocess
import tempfile
import shutil
import json
from flask import Flask, request, jsonify
from urllib.parse import urlparse

app = Flask(__name__)

@app.route("/scan", methods=["POST"])
def scan_code():
    data = request.get_json()
    if not data or "repo_url" not in data:
        return jsonify({"success": False, "error": "Missing repo_url"}), 400

    repo_url = data["repo_url"]
    gitkey = data.get("gitkey", None)

    parsed_url = urlparse(repo_url)
    # Monta a URL autenticada caso tenha gitkey
    if gitkey:
        repo_url = f"https://{gitkey}@{parsed_url.netloc}{parsed_url.path}"

    temp_dir = tempfile.mkdtemp()

    try:
        # 1. Clonar o repositório
        subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            check=True
        )

        # 2. Rodar Horusec CLI
        result = subprocess.run(
            ["horusec", "start", "-p", temp_dir, "-o", "json"],
            capture_output=True,
            text=True,
            check=True
        )

        # 3. Converter saída para JSON
        try:
            scan_result = json.loads(result.stdout)
        except json.JSONDecodeError:
            return jsonify({"success": False, "error": "Invalid JSON output from Horusec"}), 500

        return jsonify({
            "success": True,
            "results": scan_result
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.stderr}), 500

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7070)