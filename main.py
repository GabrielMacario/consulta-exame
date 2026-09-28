"""
Consulta vários exames (códigos TUSS) na API de agendamento online da Amil
e salva o retorno de cada um.

Como usar:
  1. Copie o curl do navegador (DevTools > Network > botão direito > Copy as cURL)
     e cole num arquivo chamado  curl.txt  na mesma pasta deste script.
  2. pip install requests
  3. python consulta_exames_amil.py

O script lê URL, headers, token e cookies direto do curl.txt, então quando o
token expirar é só colar um curl novo no arquivo — não precisa mexer no código.
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Exames a consultar (nome: código TUSS)
# ---------------------------------------------------------------------------
EXAMES = {"1. SÓDIO - PESQUISA E/OU DOSAGEM": "40302423",
"2. HEMOGRAMA COMPLETO": "40304361",
"3. UREIA, SORO": "40302580",
"4. TRIGLICERÍDEOS, SORO": "40302547",
"5. HEMOGLOBINA GLICADA": "40302075",
"6. HORMÔNIO TIREOESTIMULANTE (TSH), SORO": "40316521",
"7. GLICEMIA EM JEJUM": "40302040",
"8. COLESTEROL TOTAL E FRAÇÕES COM TRIGLICÉRIDES": "40302750",
"9. PROVAS DE FUNÇÃO HEPÁTICA (BILIRRUBINA TOTAL E FRAÇÕES, PROTEÍNAS TOTAIS E FRAÇÃO, FA, TGO, TGP E GAMA-PGT)": "40312151",
"10. POTÁSSIO - PESQUISA E/OU DOSAGEM": "40302318",
"11. CREATININA - PESQUISA E/OU DOSAGEM": "40301630",
"12. VITAMINA D (25 OH)": "40302830",
"13. FERRITINA, SORO": "40316270",
"14. TRANSFERRINA - PESQUISA E/OU DOSAGEM": "40302520",
"15. FERRO, SORO": "40301842",
"16. VITAMINA B12, SORO": "40316572",
"17. CÁLCIO IÔNICO, SORO": "40301419",
"18. MAGNÉSIO - PESQUISA E/OU DOSAGEM": "40302237",
"19. ÁCIDO FÓLICO, SORO": "40301087",
"20. ÁCIDO ÚRICO - PESQUISA E/OU DOSAGEM": "40301150",
"21. URINA 1+ CULTURA ANTIBIOGRAMA": "40310213",
"22. ELETROCARDIOGRAMA (ECG) CONVENCIONAL - ATÉ 12 DERIVAÇÕES": "40101010",
"23. CORTISOL BASAL, SANGUE": "40316190",
"24. INSULINA TOTAL E LIVRE": "40316963",
"25. TESTOSTERONA LIVRE, SORO": "40316505",
"26. TESTOSTERONA TOTAL, SORO": "40316513",
"27. US - ABDOME TOTAL": "40901122",
"28. ELETROCARDIOGRAMA (ECG) CONVENCIONAL - ATÉ 12 DERIVAÇÕES": "40101010",
"29. URINA 1+ CULTURA ANTIBIOGRAMA": "40310213"
}

ARQUIVO_CURL = Path(__file__).with_name("curl.txt")
PASTA_SAIDA = Path(__file__).with_name("resultados")
PAUSA_ENTRE_REQUISICOES = 1.5  # segundos, para não ser bloqueado


# ---------------------------------------------------------------------------
# Leitura do curl
# ---------------------------------------------------------------------------
def _decodificar_ansi_c(texto: str) -> str:
    """Converte escapes do formato $'...' do bash (ex.: \\u0021 -> !)."""
    texto = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), texto)
    return texto.replace("\\'", "'").replace("\\\\", "\\")


def ler_curl(caminho: Path):
    if not caminho.exists():
        sys.exit(f"Arquivo {caminho.name} não encontrado. Cole o curl nele.")

    conteudo = caminho.read_text(encoding="utf-8")

    url = re.search(r"(?:--url\s+|curl\s+)'([^']+)'", conteudo)
    if not url:
        sys.exit("Não encontrei a URL no curl.")
    url = url.group(1)

    headers = {}
    for nome, valor in re.findall(r"-H\s+'([^:]+):\s*([^']*)'", conteudo):
        headers[nome.strip()] = valor.strip()

    cookie = re.search(r"-b\s+\$'((?:[^'\\]|\\.)*)'", conteudo)
    if cookie:
        headers["cookie"] = _decodificar_ansi_c(cookie.group(1))
    else:
        cookie = re.search(r"-b\s+'([^']*)'", conteudo)
        if cookie:
            headers["cookie"] = cookie.group(1)

    return url, headers


def montar_url(url_modelo: str, tuss: str) -> str:
    """Troca o último segmento da URL (o código TUSS) pelo código desejado."""
    base = url_modelo.split("?")[0].rstrip("/")
    return base.rsplit("/", 1)[0] + "/" + tuss


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------
def consultar(sessao: requests.Session, url: str):
    resp = sessao.get(url, timeout=30)
    try:
        corpo = resp.json()
    except ValueError:
        corpo = resp.text
    return resp.status_code, corpo


def main():
    url_modelo, headers = ler_curl(ARQUIVO_CURL)
    PASTA_SAIDA.mkdir(exist_ok=True)

    sessao = requests.Session()
    sessao.headers.update(headers)

    todos = []
    for nome, tuss in EXAMES.items():
        url = montar_url(url_modelo, tuss)
        print(f"Consultando {nome} (TUSS {tuss})... ", end="", flush=True)

        try:
            status, corpo = consultar(sessao, url)
        except requests.RequestException as erro:
            status, corpo = None, f"Erro de conexão: {erro}"

        print(status)
        if status in (401, 403):
            print("  -> Token expirado ou acesso bloqueado. Gere um curl novo no navegador.")

        registro = {
            "exame": nome,
            "tuss": tuss,
            "status_http": status,
            "consultado_em": datetime.now().isoformat(timespec="seconds"),
            "resposta": corpo,
        }
        todos.append(registro)

        (PASTA_SAIDA / f"{tuss}.json").write_text(
            json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        time.sleep(PAUSA_ENTRE_REQUISICOES)

    consolidado = PASTA_SAIDA / f"todos_{datetime.now():%Y%m%d_%H%M%S}.json"
    consolidado.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in todos if r["status_http"] == 200)
    print(f"\n{ok}/{len(todos)} consultas com sucesso. Resultados em: {PASTA_SAIDA.resolve()}")


if __name__ == "__main__":
    main()