import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from parkingdsl import DSLError, Interpreter, execute
from parkingdsl.ast_nodes import DeclararVaga, Estacionar
from parkingdsl.diagnostics import Position
from parkingdsl.lexer import tokenize
from parkingdsl.parser import Parser
from parkingdsl.semantic import State

ROOT = Path(__file__).resolve().parents[1]
UTF8_ENV = dict(os.environ, PYTHONIOENCODING='utf-8')


def wrap(*lines):
    return 'estacionamento Central {\n' + '\n'.join(lines) + '\n}'


class LexicalTests(unittest.TestCase):
    def test_token_positions(self):
        tokens = tokenize('estacionamento X {\n\tvaga A1 comum\n}')
        self.assertEqual((tokens[3].kind, tokens[3].position), ('vaga', Position(2, 2)))
        self.assertEqual(tokens[-1].kind, 'EOF')

    def test_keywords_require_full_word(self):
        self.assertEqual(tokenize('vagaExtra')[0].kind, 'ID')

    def test_identifiers(self):
        self.assertEqual([t.value for t in tokenize('A a_1 Z99')[:-1]], ['A', 'a_1', 'Z99'])

    def test_forbidden_character(self):
        with self.assertRaises(DSLError) as cm:
            tokenize(wrap('vaga A1 comum;'))
        self.assertEqual((cm.exception.phase, cm.exception.code, cm.exception.position), ('léxico', 'L001', Position(2, 14)))

    def test_unclosed_plate(self):
        with self.assertRaises(DSLError) as cm:
            tokenize(wrap('entrada "ABC1234'))
        self.assertEqual((cm.exception.code, cm.exception.position), ('L002', Position(2, 9)))

    def test_invalid_plate_matrix(self):
        for plate in ('abc1234', 'ABC123', 'ABC12345', 'ABC-123', 'ÁBC1234', 'ABC 123', ''):
            with self.subTest(plate=plate), self.assertRaises(DSLError) as cm:
                tokenize(wrap(f'entrada "{plate}"'))
            self.assertEqual((cm.exception.code, cm.exception.position), ('L003', Position(2, 9)))

    def test_comments_are_not_supported(self):
        with self.assertRaises(DSLError) as cm:
            tokenize(wrap('# comentario', 'vaga A1 comum'))
        self.assertEqual(cm.exception.code, 'L001')

    def test_windows_line_endings(self):
        self.assertEqual(tokenize('vaga\r\nA1')[1].position, Position(2, 1))

    def test_plate_can_be_all_digits(self):
        self.assertEqual(tokenize('"1234567"')[0].kind, 'PLACA')


class SyntaxTests(unittest.TestCase):
    def test_ast_node_types(self):
        ast = Parser(tokenize(wrap('vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1'))).parse()
        self.assertEqual(ast.name, 'Central')
        self.assertIsInstance(ast.commands[0], DeclararVaga)
        self.assertIsInstance(ast.commands[2], Estacionar)
        self.assertEqual(ast.commands[2].position, Position(4, 1))

    def assertSyntax(self, source, code, line, column):
        with self.assertRaises(DSLError) as cm:
            Parser(tokenize(source)).parse()
        self.assertEqual((cm.exception.phase, cm.exception.code, cm.exception.position), ('sintático', code, Position(line, column)))

    def test_empty_program(self):
        self.assertSyntax('estacionamento X {}', 'S002', 1, 19)

    def test_missing_close_brace(self):
        self.assertSyntax('estacionamento X {\nvaga A1 comum', 'S001', 2, 14)

    def test_missing_em(self):
        self.assertSyntax(wrap('estacionar "ABC1234" A1'), 'S001', 2, 22)

    def test_wrong_order(self):
        self.assertSyntax(wrap('estacionar em A1 "ABC1234"'), 'S001', 2, 12)

    def test_invalid_category_is_syntax_error(self):
        self.assertSyntax(wrap('vaga A1 premium'), 'S003', 2, 9)

    def test_trailing_program(self):
        self.assertSyntax('estacionamento X { vaga A1 comum } vaga B1 pcd', 'S001', 1, 36)

    def test_case_sensitive_keywords(self):
        self.assertSyntax('Estacionamento X { vaga A1 comum }', 'S001', 1, 1)

    def test_reserved_word_cannot_be_identifier(self):
        self.assertSyntax(wrap('vaga entrada comum'), 'S001', 2, 6)

    def test_newlines_not_required(self):
        self.assertEqual(len(Parser(tokenize('estacionamento X{vaga A1 comum entrada "ABC1234"}')).parse().commands), 2)


class ValidTests(unittest.TestCase):
    def test_article_listing(self):
        run = execute((ROOT / 'examples/01_ciclo_completo.dsl').read_text(encoding='utf-8'), verify=True)
        self.assertEqual(run.state.snapshot(), dict(spaces={'A1': 'comum', 'A2': 'pcd', 'A3': 'idoso'}, present=[], occupied={}, vehicle_space={}))
        self.assertEqual([e.operation for e in run.events], ['DeclararVaga'] * 3 + ['Entrada', 'Estacionar', 'Liberar', 'Saida'])

    def test_multiple_vehicles(self):
        run = execute(wrap('vaga A1 comum', 'vaga A2 pcd', 'entrada "ABC1234"', 'entrada "DEF5678"', 'estacionar "ABC1234" em A1', 'estacionar "DEF5678" em A2'), verify=True)
        self.assertEqual(run.state.occupied, {'A1': 'ABC1234', 'A2': 'DEF5678'})

    def test_release_keeps_presence(self):
        state = execute(wrap('vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1', 'liberar A1'), verify=True).state
        self.assertEqual(state.present, {'ABC1234'})
        self.assertEqual(state.occupied, {})
        self.assertEqual(state.vehicle_space, {})

    def test_reentry(self):
        run = execute(wrap('entrada "ABC1234"', 'saida "ABC1234"', 'entrada "ABC1234"'), verify=True)
        self.assertEqual(run.state.present, {'ABC1234'})

    def test_relocation(self):
        run = execute(wrap('vaga A1 comum', 'vaga A2 idoso', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1', 'liberar A1', 'estacionar "ABC1234" em A2'), verify=True)
        self.assertEqual(run.state.occupied, {'A2': 'ABC1234'})

    def test_independent_executions(self):
        first, second = execute(wrap('entrada "ABC1234"')), execute(wrap('vaga A1 comum'))
        self.assertEqual(first.state.present, {'ABC1234'})
        self.assertEqual(second.state.present, set())

    def test_identifiers_are_case_sensitive(self):
        self.assertEqual(len(execute(wrap('vaga A1 comum', 'vaga a1 idoso')).state.spaces), 2)


class SemanticTests(unittest.TestCase):
    def assertFailure(self, prefix, command, code):
        machine = Interpreter(verify=True)
        ast = Parser(tokenize(wrap(*prefix, command, 'vaga NUNCA comum'))).parse()
        # Oráculo do estado parcial: comandos anteriores definidos manualmente no teste.
        for accepted in ast.commands[:len(prefix)]:
            machine.step(accepted)
        before = machine.state.snapshot()
        events = list(machine.events)
        with self.assertRaises(DSLError) as cm:
            machine.step(ast.commands[len(prefix)])
        self.assertEqual((cm.exception.phase, cm.exception.code, cm.exception.position), ('semântico', code, Position(len(prefix) + 2, 1)))
        self.assertEqual(machine.state.snapshot(), before)
        self.assertEqual(machine.events, events)
        machine.state.check_invariants()

    def test_duplicate_space(self):
        self.assertFailure(['vaga A1 comum'], 'vaga A1 pcd', 'E001')

    def test_undeclared_space(self):
        self.assertFailure([], 'estacionar "ABC1234" em A1', 'E002')

    def test_forward_declaration_is_rejected(self):
        machine = Interpreter()
        with self.assertRaises(DSLError) as cm:
            machine.run(Parser(tokenize(wrap('entrada "ABC1234"', 'estacionar "ABC1234" em A1', 'vaga A1 comum'))).parse())
        self.assertEqual(cm.exception.code, 'E002')
        self.assertEqual(machine.state.snapshot(), dict(spaces={}, present=['ABC1234'], occupied={}, vehicle_space={}))

    def test_duplicate_entry(self):
        self.assertFailure(['entrada "ABC1234"'], 'entrada "ABC1234"', 'E003')

    def test_absent_vehicle(self):
        self.assertFailure(['vaga A1 comum'], 'estacionar "ABC1234" em A1', 'E004')

    def test_occupied_space(self):
        self.assertFailure(['vaga A1 comum', 'entrada "ABC1234"', 'entrada "DEF5678"', 'estacionar "ABC1234" em A1'], 'estacionar "DEF5678" em A1', 'E005')

    def test_vehicle_in_two_spaces(self):
        self.assertFailure(['vaga A1 comum', 'vaga A2 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1'], 'estacionar "ABC1234" em A2', 'E006')

    def test_release_free_space(self):
        self.assertFailure(['vaga A1 comum'], 'liberar A1', 'E007')

    def test_release_undeclared_space(self):
        self.assertFailure([], 'liberar A1', 'E002')

    def test_exit_absent_vehicle(self):
        self.assertFailure([], 'saida "ABC1234"', 'E004')

    def test_exit_parked_vehicle(self):
        self.assertFailure(['vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1'], 'saida "ABC1234"', 'E008')

    def test_diagnostic_priority(self):
        self.assertFailure(['vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1'], 'estacionar "ABC1234" em A1', 'E005')
        self.assertFailure(['vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1'], 'estacionar "DEF5678" em A1', 'E004')

    def test_run_stops_and_preserves_partial_state(self):
        machine = Interpreter(verify=True)
        with self.assertRaises(DSLError):
            machine.run(Parser(tokenize(wrap('vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" em A1', 'saida "ABC1234"', 'vaga NUNCA pcd'))).parse())
        self.assertEqual(machine.state.snapshot(), dict(spaces={'A1': 'comum'}, present=['ABC1234'], occupied={'A1': 'ABC1234'}, vehicle_space={'ABC1234': 'A1'}))
        self.assertEqual(len(machine.events), 3)

    def test_inverse_index_detection(self):
        state = State(spaces={'A1': 'comum'}, present={'ABC1234'}, occupied={'A1': 'ABC1234'})
        with self.assertRaises(AssertionError):
            state.check_invariants()


class IntegrationTests(unittest.TestCase):
    def cli(self, source, *options):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'case.dsl'
            path.write_text(source, encoding='utf-8')
            return subprocess.run([sys.executable, '-m', 'parkingdsl', str(path), *options], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', env=UTF8_ENV)

    def test_json_success(self):
        result = self.cli(wrap('vaga A1 comum'), '--json')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['state']['spaces'], {'A1': 'comum'})

    def test_syntax_failure_has_zero_effects(self):
        result = self.cli(wrap('vaga A1 comum', 'entrada "ABC1234"', 'estacionar "ABC1234" A1'), '--json')
        data = json.loads(result.stdout)
        self.assertEqual((result.returncode, data['accepted_commands'], data['state']['spaces']), (1, 0, {}))

    def test_lexical_failure_has_zero_effects(self):
        result = self.cli(wrap('vaga A1 comum', '@'), '--json')
        data = json.loads(result.stdout)
        self.assertEqual((result.returncode, data['accepted_commands'], data['state']['spaces']), (1, 0, {}))

    def test_json_partial_state(self):
        result = self.cli(wrap('vaga A1 comum', 'saida "ABC1234"', 'vaga A2 pcd'), '--json')
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data['state']['spaces'], {'A1': 'comum'})
        self.assertEqual((data['error']['code'], data['error']['line'], data['error']['column']), ('E004', 3, 1))

    def test_missing_file(self):
        result = subprocess.run([sys.executable, '-m', 'parkingdsl', str(ROOT / 'missing.dsl'), '--json'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', env=UTF8_ENV)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'erro de arquivo')

    def test_tokens_and_ast_modes(self):
        for option in ('--tokens', '--ast'):
            with self.subTest(option=option):
                result = self.cli(wrap('vaga A1 comum'), option)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(json.loads(result.stdout))

    def test_bom_file(self):
        result = self.cli('\ufeff' + wrap('vaga A1 comum'), '--json')
        self.assertEqual(result.returncode, 0)

    def test_deterministic_sorting(self):
        result = self.cli(wrap('vaga Z1 comum', 'vaga A1 pcd'), '--json')
        self.assertEqual(list(json.loads(result.stdout)['state']['spaces']), ['A1', 'Z1'])

    def test_trace_and_marker(self):
        result = self.cli(wrap('vaga A1 comum', 'liberar A1'), '--trace', '--verify')
        self.assertEqual(result.returncode, 1)
        self.assertIn('001 | Vaga A1 declarada', result.stdout)
        self.assertIn('^', result.stdout)


class ModelTests(unittest.TestCase):
    def test_seeded_sequences_against_independent_model(self):
        # Oráculo deliberadamente simples: busca linear em uma lista de vagas.
        # Não usa validate(), índices inversos ou snapshots do interpretador.
        for seed in range(10):
            rng = random.Random(seed)
            slots = [['A1', None], ['A2', None], ['A3', None]]
            present, lines = set(), ['vaga A1 comum', 'vaga A2 pcd', 'vaga A3 idoso']
            expected = []
            for _ in range(120):
                plate = rng.choice(['ABC1234', 'DEF5678', 'GHI9012', 'JKL3456'])
                space = rng.choice(['A1', 'A2', 'A3'])
                op = rng.choice(['entrada', 'estacionar', 'liberar', 'saida'])
                slot = next(v for v in slots if v[0] == space)
                parked = any(v[1] == plate for v in slots)
                if op == 'entrada' and plate not in present:
                    present.add(plate)
                    lines.append(f'entrada "{plate}"')
                elif op == 'estacionar' and plate in present and slot[1] is None and not parked:
                    slot[1] = plate
                    lines.append(f'estacionar "{plate}" em {space}')
                elif op == 'liberar' and slot[1] is not None:
                    slot[1] = None
                    lines.append(f'liberar {space}')
                elif op == 'saida' and plate in present and not parked:
                    present.remove(plate)
                    lines.append(f'saida "{plate}"')
                else:
                    continue
                expected.append((set(present), {v[0]: v[1] for v in slots if v[1] is not None}))
            machine = Interpreter(verify=True)
            ast = Parser(tokenize(wrap(*lines))).parse()
            for command in ast.commands[:3]:
                machine.step(command)
            for command, (want_present, want_occupied) in zip(ast.commands[3:], expected):
                machine.step(command)
                self.assertEqual(machine.state.present, want_present)
                self.assertEqual(machine.state.occupied, want_occupied)


if __name__ == '__main__':
    unittest.main(verbosity=2)
