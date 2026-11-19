"""PR de demostracion: este test falla a proposito (IE6)."""


def test_falla_intencional():
    assert False, "Falla intencional para demostrar que el gate bloquea el merge"
