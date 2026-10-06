"""Publica un blog a partir de un archivo de texto sencillo.

Uso: python publicar.py entradas/mi-blog.txt

Formato del archivo (ver entradas/_plantilla.txt):

    titulo: Diario de CARE
    fecha: 2026-10-20
    portada: care_cover_web.png      (opcional)
    ---
    Primer párrafo.

    Segundo párrafo.

El script:
  1. crea (o reemplaza) blogs/<nombre-del-archivo>.html,
  2. rehace la lista de blogs de index.html, del más nuevo al más antiguo,
  3. regenera feed.xml con generar_rss.py.
"""
import html
import re
import sys
from datetime import date
from pathlib import Path

import generar_rss

RAIZ = Path(__file__).parent
BLOGS = RAIZ / "blogs"
INDEX = RAIZ / "index.html"
# Página que sirve de molde: se copia su cabecera, menú y pie
MOLDE = BLOGS / "hey-projects.html"
LARGO_ADELANTO = 120


def leer_entrada(ruta):
    texto = ruta.read_text(encoding="utf-8")
    if "\n---" not in texto:
        sys.exit("Falta la línea '---' que separa los datos del texto del blog.")
    cabecera, cuerpo = texto.split("\n---", 1)

    datos = {}
    for linea in cabecera.splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            datos[clave.strip().lower()] = valor.strip()

    if not datos.get("titulo"):
        sys.exit("Falta 'titulo:' en el archivo.")
    try:
        date.fromisoformat(datos.get("fecha", ""))
    except ValueError:
        sys.exit("La fecha debe tener el formato año-mes-día, por ejemplo 'fecha: 2026-10-20'.")

    # Los párrafos van separados por una línea en blanco
    parrafos = [" ".join(p.split()) for p in re.split(r"\n\s*\n", cuerpo.strip()) if p.strip()]
    if not parrafos:
        sys.exit("El blog no tiene texto debajo de '---'.")

    portada = datos.get("portada", "")
    if portada and not (RAIZ / portada).exists():
        sys.exit(f"No encuentro la portada '{portada}' en la carpeta del blog.")

    return {
        "titulo": datos["titulo"],
        "fecha": datos["fecha"],
        "portada": portada,
        "parrafos": parrafos,
    }


def crear_pagina(entrada, destino):
    molde = MOLDE.read_text(encoding="utf-8")
    titulo = html.escape(entrada["titulo"], quote=False)

    pagina = re.sub(r"<title>.*?</title>", f"<title>{titulo} | Ojiksoft</title>", molde, count=1)

    # La portada se guarda en la página para poder rehacer la tarjeta del inicio
    pagina = re.sub(r'\s*<meta name="portada"[^>]*>', "", pagina)
    if entrada["portada"]:
        pagina = pagina.replace(
            '<meta name="viewport"',
            f'<meta name="portada" content="{html.escape(entrada["portada"])}">\n    <meta name="viewport"', 1)

    # El texto admite etiquetas HTML sencillas, como <strong> o <a>
    parrafos = "\n".join(f"            <p>{p}</p>" for p in entrada["parrafos"])
    articulo = f'''<article class="blog-completo">
            <time datetime="{entrada["fecha"]}">{entrada["fecha"]}</time>
            <h1>{titulo}</h1>
{parrafos}
            <a href="../index.html" class="volver">← Back to blog</a>
        </article>'''
    pagina = re.sub(r'<article class="blog-completo">.*?</article>', lambda _: articulo, pagina, count=1, flags=re.S)

    destino.write_text(pagina, encoding="utf-8")


def adelanto(texto):
    texto = html.unescape(re.sub(r"<[^>]+>", "", texto)).strip()
    if len(texto) <= LARGO_ADELANTO:
        return html.escape(texto, quote=False)
    corte = texto[:LARGO_ADELANTO].rsplit(" ", 1)[0].rstrip(".,;:")
    return html.escape(corte, quote=False) + "…"


def leer_pagina(ruta):
    texto = ruta.read_text(encoding="utf-8")
    articulo = re.search(r'<article class="blog-completo">(.*?)</article>', texto, re.S).group(1)
    portada = re.search(r'<meta name="portada" content="([^"]*)"', texto)
    primer_parrafo = re.search(r"<p>(.*?)</p>", articulo, re.S)
    return {
        "archivo": ruta.name,
        "titulo": re.search(r"<h1>(.*?)</h1>", articulo, re.S).group(1).strip(),
        "fecha": re.search(r'<time datetime="([^"]+)"', articulo).group(1),
        "portada": html.unescape(portada.group(1)) if portada else "",
        "adelanto": adelanto(primer_parrafo.group(1)) if primer_parrafo else "",
    }


def tarjeta(blog):
    if blog["portada"]:
        portada = f'<img class="portada" src="{html.escape(blog["portada"])}" alt="">'
    else:
        portada = '<div class="portada"></div>'
    return f'''            <article class="blog">
                <a href="blogs/{blog["archivo"]}">
                    {portada}
                    <div class="blog-info">
                        <time datetime="{blog["fecha"]}">{blog["fecha"]}</time>
                        <h2>{blog["titulo"]}</h2>
                        <p>{blog["adelanto"]}</p>
                    </div>
                </a>
            </article>
'''


def rehacer_inicio():
    blogs = sorted((leer_pagina(r) for r in BLOGS.glob("*.html")),
                   key=lambda b: b["fecha"], reverse=True)
    inicio = INDEX.read_text(encoding="utf-8")
    lista = "".join(tarjeta(b) for b in blogs)
    inicio, cambios = re.subn(r'(<div class="blogs">\n).*?(        </div>\n    </main>)',
                              lambda m: m.group(1) + lista + m.group(2), inicio, count=1, flags=re.S)
    if not cambios:
        sys.exit('No encuentro la lista <div class="blogs"> en index.html.')
    INDEX.write_text(inicio, encoding="utf-8")
    return len(blogs)


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python publicar.py entradas/mi-blog.txt")
    origen = Path(sys.argv[1])
    if not origen.exists():
        sys.exit(f"No existe el archivo '{origen}'.")
    if origen.name.startswith("_"):
        sys.exit("Ese archivo es la plantilla: cópialo con otro nombre y publica la copia.")

    entrada = leer_entrada(origen)
    destino = BLOGS / f"{origen.stem}.html"
    crear_pagina(entrada, destino)
    print(f"Blog creado: blogs/{destino.name}")

    total = rehacer_inicio()
    print(f"index.html actualizado con {total} blog(s).")

    generar_rss.main()


if __name__ == "__main__":
    main()
