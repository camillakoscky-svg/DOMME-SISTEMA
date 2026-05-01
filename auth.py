"""
DOMME — Autenticação RBAC
MVP: usuários hardcoded com hash SHA-256.
Em produção: migrar para Supabase Auth ou PostgreSQL.
"""
import hashlib
from dataclasses import dataclass
from typing import Literal, Optional

PerfilType = Literal["ADMIN", "FABRICA", "CLIENTE"]


@dataclass
class Usuario:
    username: str
    perfil: PerfilType
    nome: str
    empresa: str
    senha_hash: str


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


# Em produção, isso vem de banco. Senhas iniciais — trocar antes do deploy.
USUARIOS: dict[str, Usuario] = {
    "camilla": Usuario(
        username="camilla", perfil="ADMIN",
        nome="Camilla", empresa="DOMME",
        senha_hash=_hash("domme2025"),
    ),
    "laszlo": Usuario(
        username="laszlo", perfil="FABRICA",
        nome="Equipe Laszlo", empresa="Laszlo Aromaterapia",
        senha_hash=_hash("laszlo2025"),
    ),
    "cliente_demo": Usuario(
        username="cliente_demo", perfil="CLIENTE",
        nome="Boutique Demo", empresa="Cliente Premium",
        senha_hash=_hash("demo2025"),
    ),
}


def autenticar(username: str, senha: str) -> Optional[Usuario]:
    u = USUARIOS.get(username.lower().strip())
    if u and u.senha_hash == _hash(senha):
        return u
    return None


# Matriz de permissões (RBAC)
PERMISSOES = {
    "ADMIN": {
        "motor", "cenarios", "exportacao", "proposta",
        "catalogo", "base_mp", "retirada",
        "parametros", "regras",
        "visao_caixa",
        "lucro_consolidado",
    },
    "FABRICA": {
        "catalogo_edit",
        "base_mp_edit",
        "retirada_edit",
    },
    "CLIENTE": {
        "motor",
        "exportacao",
        "proposta",
    },
}


def pode(usuario: Optional[Usuario], permissao: str) -> bool:
    if usuario is None:
        return False
    return permissao in PERMISSOES.get(usuario.perfil, set())
