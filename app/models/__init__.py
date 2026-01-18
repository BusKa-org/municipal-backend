# app/models/__init__.py
from .user import User, Aluno, Motorista, Gestor
from .geo import Ponto, Endereco, Instituicao
from .frota import Onibus
from .rota import Rota, RotaPonto, HorarioRota, DiasOperacao
from .viagem import Viagem, ViagemPonto, AlunosConfirmados
from .notificacao import Notificacao  # <--- FALTAVA ISSO
from .enum import DiaDaSemana, SentidoViagem, StatusViagem