import subprocess
import tempfile
import shutil
import json
import logging
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

HORUSEC_PATH = "/usr/local/bin/horusec"

@app.route("/scan", methods=["POST"])
def scan_code():
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("Nova requisição de scan recebida")
    
    data = request.get_json()
    if not data or "repo_url" not in data:
        logger.error("Requisição inválida: repo_url ausente")
        return jsonify({"success": False, "error": "Missing repo_url"}), 400

    repo_url = data["repo_url"]
    git_token = data.get("git_key")
    
    logger.info(f"Repository URL: {repo_url}")
    logger.info(f"Token fornecido: {'Sim' if git_token else 'Não'}")

    # Adicionar token se fornecido
    if git_token:
        if repo_url.startswith("https://"):
            repo_url = repo_url.replace("https://", f"https://{git_token}@")
            logger.info("Token adicionado à URL")

    temp_dir = tempfile.mkdtemp()
    json_output_file = Path(tempfile.mktemp(suffix=".json"))
    
    logger.info(f"Diretório temporário criado: {temp_dir}")
    logger.info(f"Arquivo de saída: {json_output_file}")

    try:
        # Clone do repositório
        logger.info("Iniciando clone do repositório...")
        clone_result = subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"✓ Clone concluído com sucesso")
        if clone_result.stdout:
            logger.debug(f"Git stdout: {clone_result.stdout}")

        # Executar Turing SAST Scan
        logger.info("Iniciando análise com Turing SAST Scan...")
        scan_result_process = subprocess.run(
            [
                HORUSEC_PATH,
                "start",
                "-p", temp_dir,
                "--output-format", "json",
                "--json-output-file", str(json_output_file)
            ],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("✓ Análise Turing SAST Scan concluída")
        
        if scan_result_process.stdout:
            logger.info(f"Scan output:\n{scan_result_process.stdout}")
        if scan_result_process.stderr:
            logger.warning(f"Scan stderr:\n{scan_result_process.stderr}")

        # Ler resultados
        logger.info("Lendo resultados da análise...")
        with open(json_output_file, "r", encoding="utf-8") as f:
            scan_result = json.load(f)
        
        # Estatísticas dos resultados
        total_vulns = len(scan_result.get("analysisVulnerabilities", []))
        logger.info(f"✓ Análise completa: {total_vulns} vulnerabilidades encontradas")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Tempo total de execução: {elapsed:.2f}s")
        logger.info("="*60)

        return jsonify({"success": True, "results": scan_result})

    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Erro no subprocess: {e.cmd}")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        
        return jsonify({
            "success": False,
            "error": "Subprocess failed",
            "stdout": e.stdout,
            "stderr": e.stderr
        }), 500

    except Exception as e:
        logger.error(f"✗ Erro inesperado: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        logger.info("Limpando arquivos temporários...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        if json_output_file.exists():
            json_output_file.unlink()
        logger.info("✓ Cleanup concluído")


@app.route("/health", methods=["GET"])
def health():
    logger.info("Health check requisitado")
    return jsonify({"status": "healthy", "service": "turing-sast-api"})


if __name__ == "__main__":
    logger.info("Iniciando Turing SAST API...")
    logger.info(f"Scanner engine: Turing SAST Scan")
    app.run(host="0.0.0.0", port=7070, debug=False)