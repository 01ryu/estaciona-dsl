# APRESENTACAO: terminal (CLI) | argumentos | leitura do .dsl | execucao e exportacao JSON

"""Interface de linha de comando e exportação determinística em JSON."""
# Bibliotecas padrão: argparse lê opções do terminal, json serializa dados,
# Path acessa arquivos e sys fornece os canais de saída/códigos do processo.
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from .diagnostics import DSLError
from .lexer import tokenize
from .parser import Parser
from .interpreter import Interpreter


def main(argv=None):
    # Define o contrato da CLI: arquivo obrigatório e modos de inspeção/execução.
    parser = argparse.ArgumentParser(description='Interpretador EstacionamentoDSL')
    parser.add_argument('file', type=Path, help='Arquivo UTF-8 com extensão .dsl')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--tokens', action='store_true', help='Exibe tokens sem executar')
    mode.add_argument('--ast', action='store_true', help='Exibe AST sem executar')
    parser.add_argument('--json', action='store_true', help='Saída estruturada')
    parser.add_argument('--trace', action='store_true', help='Lista comandos aceitos')
    parser.add_argument('--verify', action='store_true', help='Confere invariantes após cada comando')
    args = parser.parse_args(argv)
    machine = Interpreter(verify=args.verify)
    error, status = None, 'sucesso'
    source = ''
    try:
        source = args.file.read_text(encoding='utf-8-sig')
        # O pipeline é sequencial: analisar tokens, montar a árvore e só então executar.
        tokens = tokenize(source)
        if args.tokens:
            print(json.dumps([asdict(t) for t in tokens], ensure_ascii=False, indent=2))
            return 0
        program = Parser(tokens).parse()
        if args.ast:
            print(json.dumps(dict(name=program.name, commands=[dict(node=type(c).__name__, **asdict(c)) for c in program.commands]), ensure_ascii=False, indent=2))
            return 0
        machine.run(program)
    except (OSError, UnicodeError) as exc:
        if args.json:
            print(json.dumps(dict(status='erro de arquivo', error=str(exc)), ensure_ascii=False))
        else:
            print(f'Erro ao ler arquivo: {exc}', file=sys.stderr)
        return 2
    # Erros léxicos/sintáticos não executaram nada. Erros semânticos podem deixar
    # o prefixo válido no estado; por isso ainda exibimos o resultado da máquina.
    except DSLError as exc:
        error, status = exc, 'interrompido'
    # Monta uma resposta única, depois escolhe apresentação JSON ou texto.
    payload = dict(status=status, name=machine.name or None,
                   accepted_commands=len(machine.events), state=machine.state.snapshot(),
                   events=[asdict(e) for e in machine.events], error=error.as_dict() if error else None)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f'Estacionamento: {machine.name or "não executado"} | {status.upper()}')
        if args.trace:
            for event in machine.events:
                print(f'{event.number:03d} | {event.description}')
        if error:
            print(str(error))
            lines = source.splitlines()
            if 0 < error.position.line <= len(lines):
                print(lines[error.position.line - 1].replace('\t', ' '))
                print(' ' * (error.position.column - 1) + '^')
        print('VAGA             CATEGORIA  OCUPANTE')
        for space, category in sorted(machine.state.spaces.items()):
            print(f'{space:<16} {category:<10} {machine.state.occupied.get(space, "livre")}')
        print(f'Presentes: {", ".join(sorted(machine.state.present)) or "nenhum"}')
        print(f'Comandos aceitos: {len(machine.events)}')
    # Convenção de saída: 0 sucesso, 1 erro da DSL; falha de arquivo retorna 2 acima.
    return 1 if error else 0


if __name__ == '__main__':
    raise SystemExit(main())
