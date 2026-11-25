# Ponto de entrada do terminal: delega o trabalho para o pacote parkingdsl.
# O import traz a função main do nosso projeto, não de uma biblioteca externa.
from parkingdsl.main import main

# Este bloco roda quando o arquivo é executado diretamente.
# SystemExit devolve ao terminal o código de sucesso ou erro retornado por main.
if __name__ == '__main__':
    raise SystemExit(main())
