# consulta-exame

Precisava consultar cerca de 30 exames no site da Amil, mas a área logada só permite buscar um por vez. Então automatizei: o script faz a consulta de todos os códigos TUSS de uma vez e salva o retorno de cada um em JSON.

## Como usar

1. Faça login no site da Amil, abra o DevTools (aba Network), faça a busca de um exame e copie a requisição como cURL.
2. Salve o curl num arquivo `curl.txt` na pasta do projeto (no Mac: `pbpaste > curl.txt`).
3. Instale a dependência e rode:

   pip3 install requests
   python3 main.py

Os resultados ficam na pasta `resultados/`, com um arquivo por exame e um consolidado.

Para consultar outros exames, edite o dicionário `EXAMES` no `main.py`.

## Observações

- O token da sessão expira em pouco tempo. Se as consultas começarem a retornar 401, gere um curl novo.
- O `curl.txt` contém seu token, CPF e dados de contato. Nunca faça commit dele.
- Tudo está encriptado no cURL.