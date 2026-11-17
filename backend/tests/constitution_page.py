"""A small page with the same HTML patterns as Función Pública's Constitution page.

The wording is shortened or invented for the test; it is not the Constitution.
"""

TITLE_NAMES = [
    "DE LOS PRINCIPIOS",  # I, without chapters
    "DE LOS DERECHOS",  # II and the rest: chapter 1 without its label
    "DE LOS HABITANTES",
    "DE LA PARTICIPACIÓN",
    "DE LA ORGANIZACIÓN",
    "DE LA RAMA LEGISLATIVA",
    "DE LA RAMA EJECUTIVA",
    "DE LA RAMA JUDICIAL",
    "DE LAS ELECCIONES",
    "DE LOS ORGANISMOS DE CONTROL",
    "DE LA ORGANIZACIÓN TERRITORIAL",
]


def _centered(text: str) -> str:
    return f'<p align="center"><strong>{text}</strong></p>'


def _article(number: str, body: str) -> str:
    return f'<p><strong>ARTÍCULO<a name="{number}"></a> {number}.</strong> {body}</p>'


def page(
    *, article_1: str = "Colombia es un Estado social de derecho.", twelfth: str = "XII"
) -> str:
    parts = [
        '<html><body><div class="menu"><p>Menú del sitio</p></div>',
        '<div class="descripcion-contenido">',
        _centered("CONSTITUCIÓN POLITICA DE LA REPUBLICA DE COLOMBIA 1991"),
        _centered("PREAMBULO"),
        _centered("EL PUEBLO DE COLOMBIA,"),
        "<p>En ejercicio de su poder soberano decreta la siguiente:</p>",
        _centered("CONSTITUCIÓN POLITICA DE COLOMBIA"),
        _centered('<a href="x">Ver la Constitución Política de 1886</a>'),
        # Title I: only a name.
        _centered(TITLE_NAMES[0]),
        _article("1", article_1),
        "<p><button>Jurisprudencia</button>"
        '<div class="card"><div class="card-body"><p>(Ver Sentencia C-000-00)</p></div></div></p>',
        "<p>(Ver Ley 1 de 1992; Art. 1)</p>",
        # Title II with chapter 1 (no label), chapter 2 (label) and chapter 3 (name only).
        _centered(TITLE_NAMES[1]),
        _centered("DE LOS DERECHOS FUNDAMENTALES"),
        _article("11", "El derecho a la vida es inviolable. No habrá pena de muerte."),
        "<p>(Ver Ley 2 de 1993)</p>",
        _article(
            "12", "(Modificado por el Art. 1, Acto legislativo 01 de 2025). Nadie será sometido."
        ),
        "<p>Segundo inciso del artículo doce.</p>",
        "<p>(Artículo modificado por el artículo 2 del Acto Legislativo 3 de 2011)</p>",
        "<p><strong>TEXTO ANTERIOR:</strong> Redacción anterior del artículo doce.</p>",
        "<p>Inciso que la fuente imprime después de la marca.</p>",
        _article("12A", "(Artículo INEXEQUIBLE)"),
        _centered("CAPÍTULO 2."),
        _centered("DE LOS DERECHOS SOCIALES"),
        _article("13", "Elegidos por el <s>Consejo antiguo</s> Consejo nuevo."),
        "<p><strong>PARÁGRAFO .</strong></p>",
        "<p>Texto del parágrafo.</p>",
        "<p><strong>DE LAS JURISDICCIONES ESPECIALES</strong></p>",
        _article("14", "A falta de regla se aplicará la ley."),
        _centered("CAPÍTULO 3A."),
        _centered("(Capitulo adicionado por el Art. 2 del Acto Legislativo 03 de 2023)"),
        _centered("DE LA JURISDICCIÓN AGRARIA"),
        _article("14A", "Créase la jurisdicción."),
    ]
    number = 20
    for index, name in enumerate(TITLE_NAMES[2:], start=3):
        parts.append(_centered(name))
        if index == 7:
            parts += [
                _centered("DEL PRESIDENTE"),
                _centered("NOTA ACLARATORIA"),
                "<p>Los epigrafes fueron corregidos.</p>",
                _centered('"LA RAMA EJECUTIVA"'),
                _centered("CAPÍTULO I."),
            ]
        else:
            parts.append(_centered("DE LAS DISPOSICIONES GENERALES"))
        parts.append(_article(str(number), f"Texto del artículo {number}."))
        number += 1
    parts += [
        f"<p><strong>TITULO {twelfth}.</strong></p>",
        "<p><strong>DEL REGIMEN ECONÓMICO</strong></p>",
        "<p><strong>DE LAS DISPOSICIONES GENERALES</strong></p>",
        _article("332", "El Estado es propietario del subsuelo."),
        "<p><strong>TITULO XIII.</strong></p>",
        "<p><strong>DE LA REFORMA DE LA CONSTITUCION</strong></p>",
        _article("374", "La Constitución podrá ser reformada por el Congreso."),
        "<p><strong>DISPOSICIONES TRANSITORIAS</strong></p>",
        _article("TRANSITORIO 1", "No se debe cargar."),
        "</div><footer><p>Pie de página</p></footer></body></html>",
    ]
    return "\n".join(parts)
