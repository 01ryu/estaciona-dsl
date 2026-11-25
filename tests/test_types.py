import unittest
from parkingdsl import execute, DSLError, Interpreter
from parkingdsl.lexer import tokenize
from parkingdsl.parser import Parser
from parkingdsl.service import run_source


def program(body):
    return 'estacionamento T {\n' + body + '\n}'


class TypeScopeTests(unittest.TestCase):
    def expect_error(self, body, code):
        with self.assertRaises(DSLError) as cm:
            execute(program(body), verify=True)
        self.assertEqual(cm.exception.code, code)

    def test_typed_aliases(self):
        m = execute(program('vaga A1 comum definir c: veiculo = "ABC1234" definir v: vaga = A1 entrada c estacionar c em v'), verify=True)
        self.assertEqual(m.state.occupied, {'A1': 'ABC1234'})

    def test_mismatch_in_declaration(self):
        self.expect_error('vaga A1 comum definir c: veiculo = A1', 'T001')

    def test_mismatch_plate_as_space(self):
        self.expect_error('definir v: vaga = "ABC1234"', 'T001')

    def test_mismatch_operation(self):
        self.expect_error('vaga A1 comum entrada A1', 'T001')

    def test_wrong_destination_type(self):
        self.expect_error('definir c: veiculo = "ABC1234" entrada c estacionar c em c', 'T001')

    def test_undeclared_alias(self):
        self.expect_error('entrada cliente', 'T002')

    def test_forward_reference(self):
        self.expect_error('definir a: veiculo = b definir b: veiculo = "ABC1234"', 'T002')

    def test_duplicate_same_scope(self):
        self.expect_error('definir c: veiculo = "ABC1234" definir c: veiculo = "DEF5678"', 'T003')

    def test_shadow_and_restore(self):
        m = execute(program('definir c: veiculo = "ABC1234" bloco { definir c: veiculo = "DEF5678" entrada c } entrada c'))
        self.assertEqual(m.state.present, {'ABC1234', 'DEF5678'})
        self.assertEqual(m.symbols.find('c').value, 'ABC1234')

    def test_outside_scope(self):
        self.expect_error('bloco { definir c: veiculo = "ABC1234" } entrada c', 'T002')

    def test_nested_parent_lookup(self):
        m = execute(program('bloco { definir c: veiculo = "ABC1234" bloco { entrada c } }'))
        self.assertEqual(m.state.present, {'ABC1234'})

    def test_sibling_invisible(self):
        self.expect_error('bloco { definir c: veiculo = "ABC1234" } bloco { entrada c }', 'T002')

    def test_scope_cleanup_after_failure(self):
        m = Interpreter()
        with self.assertRaises(DSLError):
            m.run(Parser(tokenize(program('bloco { definir c: veiculo = "ABC1234" saida c }'))).parse())
        self.assertEqual(len(m.symbols.frames), 1)
        self.assertIsNone(m.symbols.find('c'))

    def test_global_physical_spaces_only(self):
        self.expect_error('bloco { vaga A1 comum }', 'T004')

    def test_alias_collision_does_not_mutate_state(self):
        data = run_source(program('definir A1: veiculo = "ABC1234" vaga A1 comum'))
        self.assertEqual(data['state']['spaces'], {})
        self.assertEqual(data['error']['code'], 'T003')

    def test_error_position(self):
        data = run_source(program('vaga A1 comum\ndefinir x: veiculo = A1'))
        self.assertEqual((data['error']['line'], data['error']['column']), (3, 1))

    def test_resource_depth_limit(self):
        self.expect_error('bloco {' * 33 + '}' * 33, 'S005')

    def test_invalid_annotation(self):
        self.expect_error('definir x: numero = "ABC1234"', 'S004')

    def test_service_returns_pipeline(self):
        data = run_source(program('vaga A1 comum'))
        self.assertEqual(data['status'], 'sucesso')
        self.assertEqual(data['ast']['node'], 'Program')
        self.assertEqual(data['symbols'][0]['type'], 'vaga')
        self.assertEqual(data['tokens'][-1]['kind'], 'EOF')

    def test_service_fresh_state(self):
        run_source(program('vaga A1 comum'))
        self.assertEqual(run_source(program('entrada "ABC1234"'))['state']['spaces'], {})

    def test_service_limits(self):
        for source in (None, ' ' * 65537, program('entrada "ABC1234"\n' * 3100)):
            with self.subTest(source_type=type(source).__name__), self.assertRaises(ValueError):
                run_source(source)

