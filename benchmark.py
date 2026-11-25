"""Protocolo do artigo: 5 aquecimentos e 30 repetições, por etapa."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import statistics
import time

from parkingdsl.lexer import tokenize
from parkingdsl.parser import Parser
from parkingdsl.interpreter import Interpreter

ROOT = Path(__file__).resolve().parent


def generate(n):
    if not 1 <= n <= 9_999_999:
        raise ValueError('Use entre 1 e 9.999.999 vagas.')
    lines = ['estacionamento Sintetico {']
    for i in range(1, n + 1):
        plate = f'{i:07d}'
        lines += [f'vaga V{i} comum', f'entrada "{plate}"', f'estacionar "{plate}" em V{i}',
                  f'liberar V{i}', f'saida "{plate}"']
    return '\n'.join(lines + ['}']) + '\n'


def code_hash():
    digest = hashlib.sha256()
    paths = sorted((ROOT / 'parkingdsl').glob('*.py')) + [ROOT / 'benchmark.py']
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def environment():
    memory = {}
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [(name, ctypes.c_ulonglong) for name in ('total_phys', 'avail_phys', 'total_page', 'avail_page', 'total_virtual', 'avail_virtual', 'avail_extended')]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            memory = dict(total_bytes=status.total_phys, available_bytes=status.avail_phys)
    else:
        try:
            memory = dict(total_bytes=os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE'),
                          available_bytes=os.sysconf('SC_AVPHYS_PAGES') * os.sysconf('SC_PAGE_SIZE'))
        except (ValueError, OSError, AttributeError):
            pass
    cpu = platform.processor()
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                cpu = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
        except OSError:
            pass
    return dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                implementation=platform.python_implementation(), os=platform.platform(),
                cpu=cpu or 'não identificado', logical_cpus=os.cpu_count(), memory=memory,
                source_sha256=code_hash(), revision_method='SHA-256 dos nomes e bytes dos módulos parkingdsl/*.py e benchmark.py')


def measure(source):
    a = time.perf_counter_ns()
    tokens = tokenize(source)
    b = time.perf_counter_ns()
    ast = Parser(tokens).parse()
    c = time.perf_counter_ns()
    machine = Interpreter(verify=False)
    machine.run(ast)
    d = time.perf_counter_ns()
    # Fora do intervalo: valida o resultado sem contaminar a medição por etapa.
    machine.state.check_invariants()
    assert not machine.state.present and not machine.state.occupied
    return [(b - a) / 1e6, (c - b) / 1e6, (d - c) / 1e6, (d - a) / 1e6]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', type=int, nargs='+', default=[10, 100, 1000])
    parser.add_argument('--warmup', type=int, default=5)
    parser.add_argument('--repetitions', type=int, default=30)
    args = parser.parse_args(argv)
    if args.warmup < 0 or args.repetitions < 1 or any(not 1 <= n <= 9_999_999 for n in args.sizes):
        parser.error('Tamanhos positivos até 9.999.999, warmup >= 0 e repetitions >= 1.')
    result = dict(environment=environment(), warmup=args.warmup, repetitions=args.repetitions,
                  percentile_method='nearest-rank: sorted[ceil(0.95*N)-1]',
                  invariants_inside_timing=False, event_log_inside_timing=True,
                  gc_policy='coletor de lixo padrão habilitado', configurations=[], samples=[])
    for n in args.sizes:
        source = generate(n)
        for _ in range(args.warmup):
            measure(source)
        samples = [measure(source) for _ in range(args.repetitions)]
        summary = dict(spaces=n, commands=5 * n, bytes=len(source.encode('utf-8')))
        for j, stage in enumerate(('lexer', 'parser', 'interpreter', 'total')):
            values = sorted(row[j] for row in samples)
            summary[stage + '_median_ms'] = statistics.median(values)
            summary[stage + '_p95_ms'] = values[math.ceil(0.95 * len(values)) - 1]
        result['configurations'].append(summary)
        result['samples'] += [dict(spaces=n, repetition=i + 1, **dict(zip(('lexer_ms', 'parser_ms', 'interpreter_ms', 'total_ms'), row))) for i, row in enumerate(samples)]
        print(f'{n:4d} vagas | {5*n:5d} comandos | mediana {summary["total_median_ms"]:.3f} ms | p95 {summary["total_p95_ms"]:.3f} ms')
    directory = ROOT / 'results'
    directory.mkdir(exist_ok=True)
    (directory / 'benchmark.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(result['configurations'][0]))
    writer.writeheader()
    writer.writerows(result['configurations'])
    (directory / 'benchmark.csv').write_text(stream.getvalue(), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
