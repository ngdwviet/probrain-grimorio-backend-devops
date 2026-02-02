"""
Models (Pydantic).

Schema validado de magia e regras condicionais (campos dinâmicos).
Garante integridade e consistência dos dados.
"""

from __future__ import annotations

from typing import List, Optional, Literal, Tuple
from pydantic import BaseModel, Field, model_validator


EscolaMagia = Literal[
    "Abjuração",
    "Conjuração",
    "Adivinhação",
    "Encantamento",
    "Evocação",
    "Ilusão",
    "Necromancia",
    "Transmutação",
]

TipoMagia = Literal["ataque", "suporte", "controle", "utilidade"]
Componente = Literal["V", "S", "M"]


class DanoEscala(BaseModel):
    base_dados: str = Field(..., examples=["8d6"])
    slot_base: int = Field(..., ge=0, le=9)
    incremento_por_slot: str = Field(..., examples=["1d6"])

    @staticmethod
    def _parse_dice(dice: str) -> Tuple[int, int]:
        try:
            n, d = dice.lower().split("d")
            return int(n), int(d)
        except Exception:
            raise ValueError(f"Formato de dado inválido: {dice}. Use 'XdY' (ex.: 8d6).")

    def calcular_para_slot(self, nivel_slot: int) -> str:
        if nivel_slot < self.slot_base:
            raise ValueError(f"nivel_slot ({nivel_slot}) não pode ser menor que slot_base ({self.slot_base}).")

        base_n, base_d = self._parse_dice(self.base_dados)
        inc_n, inc_d = self._parse_dice(self.incremento_por_slot)

        if base_d != inc_d:
            raise ValueError("Incremento deve ter o mesmo tipo de dado do dano base (ex.: 8d6 e +1d6).")

        diff = nivel_slot - self.slot_base
        total_n = base_n + diff * inc_n
        return f"{total_n}d{base_d}"


class Magia(BaseModel):
    id: str
    nome: str = Field(..., min_length=1)
    nivel: int = Field(..., ge=0, le=9)
    escola: EscolaMagia

    tempo_conjuracao: str
    alcance: str
    duracao: str

    componentes: List[Componente] = Field(default_factory=list)

    ritual: bool = False
    concentracao: bool = False

    material_descricao: Optional[str] = None
    material_com_custo: bool = False
    custo_em_ouro: Optional[int] = Field(default=None, ge=0)

    descricao: str
    tipo: TipoMagia = "utilidade"
    dano_escala: Optional[DanoEscala] = None

    @model_validator(mode="after")
    def validar_regras_dinamicas(self):
        comps = set(self.componentes)

        if self.material_com_custo:
            if "M" not in comps:
                raise ValueError("material_com_custo=True exige componente 'M' em componentes.")
            if self.custo_em_ouro is None or self.custo_em_ouro <= 0:
                raise ValueError("custo_em_ouro é obrigatório e deve ser > 0 quando material_com_custo=True.")

        return self


class MagiaCreate(BaseModel):
    nome: str
    nivel: int = Field(..., ge=0, le=9)
    escola: EscolaMagia
    tempo_conjuracao: str
    alcance: str
    duracao: str
    componentes: List[Componente] = Field(default_factory=list)

    ritual: bool = False
    concentracao: bool = False

    material_descricao: Optional[str] = None
    material_com_custo: bool = False
    custo_em_ouro: Optional[int] = Field(default=None, ge=0)

    descricao: str
    tipo: TipoMagia = "utilidade"
    dano_escala: Optional[DanoEscala] = None


class MagiaUpdate(BaseModel):
    nome: Optional[str] = None
    nivel: Optional[int] = Field(default=None, ge=0, le=9)
    escola: Optional[EscolaMagia] = None
    tempo_conjuracao: Optional[str] = None
    alcance: Optional[str] = None
    duracao: Optional[str] = None
    componentes: Optional[List[Componente]] = None

    ritual: Optional[bool] = None
    concentracao: Optional[bool] = None

    material_descricao: Optional[str] = None
    material_com_custo: Optional[bool] = None
    custo_em_ouro: Optional[int] = Field(default=None, ge=0)

    descricao: Optional[str] = None
    tipo: Optional[TipoMagia] = None
    dano_escala: Optional[DanoEscala] = None
