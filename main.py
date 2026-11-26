# GUIA DE FALA PARA APRESENTACAO / TREINO
# Este é o ponto de entrada para executar o projeto pelo terminal com python main.py.
# Ele encaminha a execução para a função main dentro do pacote parkingdsl.
# A lógica do interpretador fica dividida nos módulos do pacote.

# Ponto de entrada do terminal: delega o trabalho para o pacote parkingdsl.
# O import traz a função main do nosso projeto, não de uma biblioteca externa.
from parkingdsl.main import main

# Este bloco roda quando o arquivo é executado diretamente.
# SystemExit devolve ao terminal o código de sucesso ou erro retornado por main.
if __name__ == '__main__':
    raise SystemExit(main())
