"""The laws NEXO loads from Función Pública's Gestor Normativo (owner choice of
2026-11-24: a fixed list of key laws for transparency, public contracting,
participation and Congress, read article by article like the Constitution).

Each page id was checked on 2026-11-24 by downloading the page and reading its
title (Ley 610 de 2000 and Ley 1952 de 2019 added the same day, 17 laws).
To add a law, add it here and run the reader's tests against its page.
Decreto 111 de 1996 is not listed: it reproduces a whole statute inside its
article 1 and needs a reader of its own.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StatuteSpec:
    gestor_id: int
    number: str
    year: int

    @property
    def slug(self) -> str:
        return f"ley-{self.number}-de-{self.year}"

    @property
    def page_url(self) -> str:
        return f"https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i={self.gestor_id}"


STATUTES = (
    StatuteSpec(11368, "5", 1992),  # Reglamento del Congreso
    StatuteSpec(304, "80", 1993),  # Estatuto General de Contratación
    StatuteSpec(330, "134", 1994),  # Mecanismos de participación ciudadana
    StatuteSpec(327, "152", 1994),  # Ley Orgánica del Plan de Desarrollo
    StatuteSpec(186, "489", 1998),  # Organización de la administración pública
    StatuteSpec(5725, "610", 2000),  # Procesos de responsabilidad fiscal
    StatuteSpec(14861, "909", 2004),  # Empleo público y carrera administrativa
    StatuteSpec(184686, "1150", 2007),  # Eficiencia y transparencia en la contratación
    StatuteSpec(41249, "1437", 2011),  # Código de Procedimiento Administrativo (CPACA)
    StatuteSpec(43292, "1474", 2011),  # Estatuto Anticorrupción
    StatuteSpec(49981, "1581", 2012),  # Protección de datos personales
    StatuteSpec(56882, "1712", 2014),  # Transparencia y acceso a la información pública
    StatuteSpec(65334, "1755", 2015),  # Derecho de petición
    StatuteSpec(65335, "1757", 2015),  # Participación democrática
    StatuteSpec(87302, "1909", 2018),  # Estatuto de la Oposición
    StatuteSpec(90324, "1952", 2019),  # Código General Disciplinario
    StatuteSpec(175606, "2195", 2022),  # Transparencia, prevención y lucha contra la corrupción
)
