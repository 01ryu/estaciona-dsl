# APRESENTACAO: regras de validade | estado do estacionamento | vaga ocupada, veiculo ausente
# Valida antes de alterar: liberar vaga nao registra saida do veiculo.

"""Estado S=(V,P,O), índice inverso e pré-condições sem efeitos colaterais."""
from dataclasses import dataclass, field
from .ast_nodes import DeclararVaga, Entrada, Estacionar, Liberar, Saida
from .diagnostics import DSLError


@dataclass
# Estado físico em memória: vagas/categorias, veículos presentes e ocupação.
# vehicle_space é o índice inverso: permite descobrir a vaga de um veículo.
class State:
    spaces: dict[str, str] = field(default_factory=dict)
    present: set[str] = field(default_factory=set)
    occupied: dict[str, str] = field(default_factory=dict)
    vehicle_space: dict[str, str] = field(default_factory=dict)

    # Invariantes são condições que devem permanecer verdadeiras após operações.
    # Por exemplo: todo ocupante está presente, e um veículo não ocupa duas vagas.
    def check_invariants(self):
        assert self.occupied.keys() <= self.spaces.keys(), 'Vaga não declarada ocupada'
        assert set(self.occupied.values()) <= self.present, 'Ocupante ausente'
        assert len(set(self.occupied.values())) == len(self.occupied), 'Ocupação não injetiva'
        assert self.vehicle_space == {p: v for v, p in self.occupied.items()}, 'Índice inverso inconsistente'

    # Produz uma representação ordenada, útil para comparar testes e exibir JSON.
    def snapshot(self):
        return dict(spaces=dict(sorted(self.spaces.items())), present=sorted(self.present),
                    occupied=dict(sorted(self.occupied.items())),
                    vehicle_space=dict(sorted(self.vehicle_space.items())))


# Consulta as pré-condições sem alterar o estado.
# Só depois desta função retornar o interpretador pode aplicar o comando.
def validate(command, state):
    def fail(code, message):
        raise DSLError('semântico', code, message, command.position)
    if isinstance(command, DeclararVaga):
        if command.space in state.spaces:
            fail('E001', f'Vaga {command.space} já declarada.')
    elif isinstance(command, Entrada):
        if command.plate in state.present:
            fail('E003', f'Veículo {command.plate} já está presente.')
    elif isinstance(command, Estacionar):
        # Ordem de diagnóstico explicitamente definida no artigo.
        if command.space not in state.spaces:
            fail('E002', f'Vaga {command.space} inexistente ou ainda não declarada.')
        if command.plate not in state.present:
            fail('E004', f'Veículo {command.plate} ausente.')
        if command.space in state.occupied:
            fail('E005', f'Vaga {command.space} ocupada.')
        if command.plate in state.vehicle_space:
            fail('E006', f'Veículo {command.plate} já ocupa a vaga {state.vehicle_space[command.plate]}.')
    elif isinstance(command, Liberar):
        if command.space not in state.spaces:
            fail('E002', f'Vaga {command.space} inexistente ou ainda não declarada.')
        if command.space not in state.occupied:
            fail('E007', f'Vaga {command.space} já está livre.')
    elif isinstance(command, Saida):
        if command.plate not in state.present:
            fail('E004', f'Veículo {command.plate} ausente.')
        if command.plate in state.vehicle_space:
            fail('E008', f'Libere a vaga {state.vehicle_space[command.plate]} antes da saída de {command.plate}.')
    else:
        raise TypeError(f'Nó de AST não suportado: {type(command).__name__}')
