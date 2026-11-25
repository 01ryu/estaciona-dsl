from python_api import Parking

p = Parking('Central')
p.declare('A1', 'comum')
p.declare('A2', 'pcd')
p.declare('A3', 'idoso')
p.enter('ABC1234')
p.park('ABC1234', 'A1')
p.release('A1')
p.leave('ABC1234')
