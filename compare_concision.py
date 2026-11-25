"""Conta o cenário inteiro, incluindo importação/criação em Python e bloco na DSL."""
import json
from pathlib import Path
from parkingdsl import execute
from cenario_python import p

ROOT = Path(__file__).resolve().parent


def metrics(path):
    text = path.read_text(encoding='utf-8').replace('\r\n', '\n')
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    return dict(nonempty_noncomment_lines=len(lines), characters=len('\n'.join(lines)))


def main():
    dsl_path = ROOT / 'examples/01_ciclo_completo.dsl'
    dsl = execute(dsl_path.read_text(encoding='utf-8'), verify=True)
    assert dsl.state.snapshot() == p.machine.state.snapshot()
    assert [e.operation for e in dsl.events] == [e.operation for e in p.machine.events]
    dm, pm = metrics(dsl_path), metrics(ROOT / 'cenario_python.py')
    infrastructure = dict(dsl_modules=sum(len(path.read_text(encoding='utf-8').splitlines()) for path in (ROOT / 'parkingdsl').glob('*.py')),
                          python_adapter=len((ROOT / 'python_api.py').read_text(encoding='utf-8').splitlines()))
    result = dict(scenario='Listagem 1 do artigo', dsl=dm, python=pm,
                  line_ratio=dm['nonempty_noncomment_lines'] / pm['nonempty_noncomment_lines'],
                  character_ratio=dm['characters'] / pm['characters'],
                  infrastructure_physical_lines=infrastructure, equivalent_state_and_operation_types=True,
                  convention='Sem linhas vazias/comentários; LF entre linhas, sem LF final. Sem reformatação. Conta delimitadores/importações. Adapter Python depende do núcleo comum; não é implementação independente. Não mede usabilidade.')
    (ROOT / 'results/concision.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
