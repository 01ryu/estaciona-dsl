"""Executa unittest e salva evidências por teste e por família."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import unittest


# Estende o relatório do unittest para guardar resultado e duração de cada método.
class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def startTest(self, test):
        self.started = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        failed = any(t.id() == test.id() for t, _ in self.failures + self.errors)
        # Registra também falhas de subtestes, cujo identificador inclui o pai.
        failed = failed or any(t.id().startswith(test.id() + ' ') for t, _ in self.failures + self.errors)
        self.records.append(dict(test=test.id(), family=type(test).__name__,
                                 status='falhou' if failed else 'passou', seconds=time.perf_counter() - self.started))
        super().stopTest(test)


# Descobre os testes e grava evidências por método e família, sem inflar subcasos.
def main():
    root = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(root / 'tests'))
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    families = {}
    for family in sorted({r['family'] for r in result.records}):
        counts = Counter(r['status'] for r in result.records if r['family'] == family)
        families[family] = dict(total=sum(counts.values()), passed=counts['passou'], failed=counts['falhou'])
    report = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
                  total=result.testsRun, passed=sum(r['status'] == 'passou' for r in result.records),
                  failures=len(result.failures), errors=len(result.errors),
                  successful=result.wasSuccessful(), seconds=time.perf_counter() - started,
                  families=families, tests=result.records,
                  failures_detail=[dict(test=t.id(), detail=detail) for t, detail in result.failures + result.errors])
    (root / 'results').mkdir(exist_ok=True)
    (root / 'results/test_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
