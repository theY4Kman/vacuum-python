class VacuumError(Exception):
    pass


class VacuumInputError(VacuumError, ValueError):
    pass


class VacuumFatalError(VacuumError):
    pass
