"""Genera feed.xml (RSS 2.0) a partir de los blogs de la carpeta blogs/.

Uso: python generar_rss.py
Vuelve a ejecutarlo cada vez que publiques o edites un blog.
"""
import html
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

# Cambia esto por la dirección real del sitio cuando lo publiques (sin "/" al final)
SITIO = "https://kijodev.github.io"
TITULO = "Ojiksoft"
DESCRIPCION = "Ojiksoft blog about web and game development."

RAIZ = Path(__file__).parent


def leer_blog(ruta):
    texto = ruta.read_text(encoding="utf-8")
    articulo = re.search(r'<article class="blog-completo">(.*?)</article>', texto, re.S).group(1)
    titulo = re.search(r"<h1>(.*?)</h1>", articulo, re.S).group(1).strip()
    fecha = re.search(r'<time datetime="([^"]+)"', articulo).group(1)
    parrafos = re.findall(r"<p>.*?</p>", articulo, re.S)
    resumen = re.sub(r"<[^>]+>", "", parrafos[0]).strip() if parrafos else ""
    return {
        "titulo": html.unescape(titulo),
        "fecha": datetime.fromisoformat(fecha).replace(tzinfo=timezone.utc),
        "url": f"{SITIO}/blogs/{ruta.name}",
        "resumen": html.unescape(resumen),
        "contenido": "\n".join(parrafos),
    }


def item(blog):
    e = lambda s: html.escape(s, quote=False)
    return f"""    <item>
      <title>{e(blog["titulo"])}</title>
      <link>{blog["url"]}</link>
      <guid isPermaLink="true">{blog["url"]}</guid>
      <pubDate>{format_datetime(blog["fecha"])}</pubDate>
      <description>{e(blog["resumen"])}</description>
      <content:encoded><![CDATA[{blog["contenido"]}]]></content:encoded>
    </item>"""


def main():
    blogs = sorted((leer_blog(r) for r in (RAIZ / "blogs").glob("*.html")),
                   key=lambda b: b["fecha"], reverse=True)
    ultima = blogs[0]["fecha"] if blogs else datetime.now(timezone.utc)
    items = "\n".join(item(b) for b in blogs)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{TITULO}</title>
    <link>{SITIO}/</link>
    <description>{DESCRIPCION}</description>
    <language>en</language>
    <lastBuildDate>{format_datetime(ultima)}</lastBuildDate>
    <atom:link href="{SITIO}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITIO}/ojiksoft_logo_final.png</url>
      <title>{TITULO}</title>
      <link>{SITIO}/</link>
    </image>
{items}
  </channel>
</rss>
"""
    (RAIZ / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"feed.xml generado con {len(blogs)} blog(s).")


if __name__ == "__main__":
    main()
