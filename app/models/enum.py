import enum

class DiaDaSemana(enum.Enum):
    SEG = "SEG"
    TER = "TER"
    QUA = "QUA"
    QUI = "QUI"
    SEX = "SEX"
    SAB = "SAB"
    DOM = "DOM"

class SentidoViagem(enum.Enum):
    IDA = "IDA"
    VOLTA = "VOLTA"
    CIRCULAR = "CIRCULAR"

class StatusViagem(enum.Enum):
    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"

class UserRole(enum.Enum):
    USER = "USER"
    ALUNO = "ALUNO"
    MOTORISTA = "MOTORISTA"
    GESTOR = "GESTOR"
    
    def __str__(self):
        return self.value