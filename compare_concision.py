"""Conta o cenário inteiro, incluindo importação/criação em Python e bloco na DSL."""
import json
from pathlib import Path
from parkingdsl import execute
import runpy

ROOT = Path(__file__).resolve().parent


# Conta linhas e caracteres sob uma convenção fixa; isso não mede facilidade de uso.
def metrics(path):
    text = path.read_text(encoding='utf-8').replace('\r\n', '\n')
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    return dict(nonempty_noncomment_lines=len(lines), characters=len('\n'.join(lines)))


# Compara três pares conhecidos, verificando equivalência antes de registrar medidas.
def main():
    scenarios = []
    for name, python_file in [('01_ciclo_completo', 'cenario_python.py'), ('02_ocupacao', 'examples/02_ocupacao.py'), ('03_realocacao', 'examples/03_realocacao.py')]:
        dsl_path = ROOT / 'examples' / (name + '.dsl')
        dsl = execute(dsl_path.read_text(encoding='utf-8'), verify=True)
        p = runpy.run_path(str(ROOT / python_file))['p']
        assert dsl.state.snapshot() == p.machine.state.snapshot()
        assert [e.operation for e in dsl.events] == [e.operation for e in p.machine.events]
        dm, pm = metrics(dsl_path), metrics(ROOT / python_file)
        scenarios.append(dict(scenario=name, dsl=dm, python=pm,
                              line_ratio=dm['nonempty_noncomment_lines']/pm['nonempty_noncomment_lines'],
                              character_ratio=dm['characters']/pm['characters'],
                              equivalent_state_and_operation_types=True))
    infrastructure = dict(dsl_modules=sum(len(path.read_text(encoding='utf-8').splitlines()) for path in (ROOT/'parkingdsl').glob('*.py')),
                          python_adapter=len((ROOT/'python_api.py').read_text(encoding='utf-8').splitlines()))
    result = dict(scenarios=scenarios, infrastructure_physical_lines=infrastructure,
                  convention='Tres pares fixos: ciclo, ocupacao e realocacao. Sem linhas vazias/comentarios; LF entre linhas, sem LF final. Inclui importacoes e delimitadores. Adaptador compartilha o nucleo. Nao e implementacao independente, nao mede usabilidade nem concisao dos recursos de tipos/escopos.')
    (ROOT / 'results/concision.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
