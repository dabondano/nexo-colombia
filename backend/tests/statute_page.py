"""Small pages with the HTML patterns of Función Pública's law pages.

The wording is invented for the tests; it is not any law's.
"""


def bold(text: str) -> str:
    return f'<p align="center"><strong>{text}</strong></p>'


def plain(text: str) -> str:
    return f"<p>{text}</p>"


def article(label: str, body: str) -> str:
    return f"<p><strong>{label}.</strong> {body}</p>"


def page(*body: str, heading: str = "LEY 9999 DE 2020", enacting: str = "DECRETA:") -> str:
    parts = [
        '<html><body><div class="descripcion-contenido">',
        bold(heading),
        bold("(Marzo 6)"),
        plain("(Ver Ley 1 de 2021)"),
        bold('"Por medio de la cual se dictan normas de ejemplo"'),
        bold("EL CONGRESO DE COLOMBIA"),
        bold(enacting),
        *body,
        bold("EL PRESIDENTE DEL HONORABLE SENADO DE LA REPÚBLICA"),
        bold("PERSONA DE EJEMPLO"),
        bold("PUBLÍQUESE Y CÚMPLASE"),
        plain("NOTA: Publicada en el Diario Oficial 99.999 de marzo 6 de 2020."),
        # Pages sometimes append other text after the signatures: never read.
        bold("CAPÍTULO III"),
        article("ARTÍCULO 108", "Texto de otra ley agregado por el editor."),
        "</div></body></html>",
    ]
    return "".join(parts)


SAMPLE_LAW = page(
    bold("TÍTULO I"),
    bold("DISPOSICIONES GENERALES"),
    article("ARTÍCULO 1", "Objeto. Esta ley de ejemplo regula el acceso a documentos de ejemplo."),
    plain("(Modificado por el art. 1 de la Ley 1 de 2021.)"),
    bold("CAPÍTULO I"),
    bold("DE LOS PRINCIPIOS"),
    article("ARTÍCULO 2", "Principios. Toda información de ejemplo es pública."),
    bold("TÍTULO II"),
    bold("DISPOSICIONES FINALES"),
    article("ARTÍCULO 3", "Vigencia. Esta ley de ejemplo rige desde su publicación."),
)
