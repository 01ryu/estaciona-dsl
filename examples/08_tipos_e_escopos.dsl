estacionamento Campus {
  vaga A1 comum
  vaga A2 pcd
  vaga A3 idoso
  vaga B1 comum
  vaga B2 comum
  vaga B3 comum
  definir cliente: veiculo = "ABC1234"
  definir destino: vaga = A1
  entrada cliente
  estacionar cliente em destino
  bloco {
    definir cliente: veiculo = "DEF5678"
    definir destino: vaga = B2
    entrada cliente
    estacionar cliente em destino
  }
  liberar destino
  saida cliente
}
