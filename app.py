from flask import Flask, request, render_template_string
from urllib.parse import urlparse, urljoin
from urllib.request import (
    Request,
    build_opener,
    HTTPRedirectHandler,
)
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
import socket
import ipaddress

app = Flask(__name__)

MAX_LINKS = 10
MAX_IMAGES = 10
TIMEOUT = 5
MAX_HTML_SIZE = 1_000_000


# No seguim redireccions automàticament.
class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = build_opener(NoRedirectHandler())


# Disseny de la pàgina
PAGE = """
<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>ShopGuard — Web Health Checker</title>

<meta name="description"
content="Comprova l'estat HTTP, els enllaços i les imatges
de la teva pàgina web amb ShopGuard.">

<style>
:root {
    --bg: #0b1020;
    --panel: #131c30;
    --panel2: #19243b;
    --green: #58edb1;
    --text: #f2f5ff;
    --muted: #a7b2ca;
    --border: #293650;
    --red: #ff7e8a;
    --yellow: #ffd479;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background:
        radial-gradient(
            ellipse at top,
            #182b43 0%,
            var(--bg) 55%
        );
    color: var(--text);
    font-family: Inter, system-ui, Arial, sans-serif;
    min-height: 100vh;
}

header {
    border-bottom: 1px solid var(--border);
    background: rgba(11, 16, 32, 0.85);
}

nav {
    max-width: 1100px;
    margin: auto;
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 23px;
    font-weight: 850;
    letter-spacing: -1px;
}

.logo span {
    color: var(--green);
}

.pill {
    color: var(--green);
    border: 1px solid #326b5c;
    border-radius: 30px;
    padding: 7px 12px;
    font-size: 12px;
}

main {
    max-width: 1000px;
    padding: 65px 22px;
    margin: auto;
}

.hero {
    text-align: center;
    margin-bottom: 40px;
}

.eyebrow {
    color: var(--green);
    text-transform: uppercase;
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 800;
}

h1 {
    font-size: clamp(36px, 7vw, 64px);
    letter-spacing: -2px;
    line-height: 1.05;
    margin: 18px 0;
}

h1 span {
    color: var(--green);
}

.hero p {
    max-width: 610px;
    margin: 0 auto;
    line-height: 1.8;
    color: var(--muted);
}

.scanner {
    max-width: 760px;
    margin: 35px auto 0;
    padding: 10px;
    display: flex;
    gap: 10px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    box-shadow: 0 20px 70px #0003;
}

input {
    flex: 1;
    min-width: 0;
    padding: 17px;
    color: white;
    background: transparent;
    border: 0;
    outline: none;
    font-size: 15px;
}

input::placeholder {
    color: #7e8ba5;
}

button {
    background: var(--green);
    color: #071a14;
    border: 0;
    padding: 0 23px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 14px;
    cursor: pointer;
}

button:hover {
    filter: brightness(1.08);
}

button:disabled {
    opacity: 0.6;
    cursor: wait;
}

.hint {
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-top: 15px;
}

.features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 55px;
}

.card {
    background: linear-gradient(145deg, var(--panel), #10182a);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 23px;
}

.icon {
    font-size: 27px;
}

.card h3 {
    margin: 14px 0 8px;
    font-size: 17px;
}

.card p {
    color: var(--muted);
    line-height: 1.7;
    font-size: 13px;
    margin-bottom: 0;
}

.results {
    margin-top: 40px;
}

.results h2 {
    font-size: 27px;
}

.summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 20px 0;
}

.stat {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 20px;
}

.stat strong {
    display: block;
    font-size: 28px;
    margin-bottom: 5px;
}

.stat span {
    color: var(--muted);
    font-size: 12px;
}

.section {
    margin-top: 20px;
    padding: 22px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 15px;
}

.section h3 {
    margin-top: 0;
}

.row {
    padding: 13px 0;
    border-bottom: 1px solid var(--border);
    overflow-wrap: anywhere;
    line-height: 1.6;
    font-size: 13px;
}

.row:last-child {
    border-bottom: 0;
}

.ok {
    color: var(--green);
}

.bad {
    color: var(--red);
}

.warn {
    color: var(--yellow);
}

.url {
    color: #b9caff;
    overflow-wrap: anywhere;
}

.notice {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.7;
    margin-top: 18px;
}

footer {
    text-align: center;
    padding: 30px 20px;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 12px;
}

@media(max-width: 650px) {
    main {
        padding-top: 40px;
    }

    .features {
        grid-template-columns: 1fr;
    }

    .scanner {
        flex-direction: column;
    }

    input {
        padding: 15px 12px;
    }

    button {
        padding: 16px;
    }

    .summary {
        grid-template-columns: 1fr;
    }

    nav {
        padding: 16px;
    }
}
</style>
</head>

<body>

<header>
<nav>
    <div class="logo">🛡️ Shop<span>Guard</span></div>
    <div class="pill">WEB HEALTH CHECKER</div>
</nav>
</header>

<main>

<section class="hero">
    <div class="eyebrow">Web diagnostics made simple</div>

    <h1>La salut de la teva web,<br>
    <span>d'un cop d'ull.</span></h1>

    <p>
        Comprova l'estat HTTP de la teva pàgina i detecta
        enllaços i imatges que poden donar problemes.
        Resultats senzills, sense complicacions.
    </p>

    <form class="scanner" method="post">
        <input
            type="text"
            name="website"
            placeholder="https://elteudomini.com"
            value="{{ website }}"
            aria-label="Adreça de la web"
            required
        >
        <button type="submit">🔍 Analitzar web</button>
    </form>

    <div class="hint">
        Analitza només webs públiques que tinguis permís per comprovar.
    </div>
</section>

<section class="features">

    <article class="card">
        <div class="icon">🌐</div>
        <h3>Estat de la web</h3>
        <p>
            Comprova si el servidor respon i mostra el codi HTTP
            retornat per la pàgina.
        </p>
    </article>

    <article class="card">
        <div class="icon">🔗</div>
        <h3>Enllaços</h3>
        <p>
            Revisa una selecció d'enllaços interns per trobar
            pàgines que retornin errors.
        </p>
    </article>

    <article class="card">
        <div class="icon">🖼️</div>
        <h3>Imatges</h3>
        <p>
            Comprova una selecció d'imatges de la mateixa web
            per detectar recursos que fallen.
        </p>
    </article>

</section>

{% if error %}
<section class="section">
    <h3 class="bad">⚠️ No s'ha pogut analitzar</h3>
    <p>{{ error }}</p>
</section>
{% endif %}

{% if report %}
<section class="results" id="results">

    <h2>📊 Informe de l'anàlisi</h2>

    <p class="url">{{ report.url }}</p>

    <div class="summary">
        <div class="stat">
            <strong>{{ report.home_status }}</strong>
            <span>Estat HTTP de la pàgina</span>
        </div>

        <div class="stat">
            <strong>{{ report.links_checked }}</strong>
            <span>Enllaços comprovats</span>
        </div>

        <div class="stat">
            <strong>{{ report.images_checked }}</strong>
            <span>Imatges comprovades</span>
        </div>
    </div>

    <div class="section">
        <h3>🌐 Resultat de la pàgina</h3>
        <p class="{{ report.home_class }}">
            {{ report.home_message }}
        </p>
    </div>

    <div class="section">
        <h3>🔗 Enllaços interns</h3>

        {% if report.links %}
            {% for item in report.links %}
            <div class="row">
                <span class="{{ item.css }}">
                    {{ item.symbol }} {{ item.message }}
                </span>
                <br>
                <span class="url">{{ item.url }}</span>
            </div>
            {% endfor %}
        {% else %}
            <p>No s'han trobat enllaços interns per comprovar.</p>
        {% endif %}
    </div>

    <div class="section">
        <h3>🖼️ Imatges</h3>

        {% if report.images %}
            {% for item in report.images %}
            <div class="row">
                <span class="{{ item.css }}">
                    {{ item.symbol }} {{ item.message }}
                </span>
                <br>
                <span class="url">{{ item.url }}</span>
            </div>
            {% endfor %}
        {% else %}
            <p>No s'han trobat imatges internes per comprovar.</p>
        {% endif %}
    </div>

    <p class="notice">
        Aquest informe és una comprovació limitada i no garanteix
        que la web sigui segura. Alguns servidors bloquegen les
        comprovacions automàtiques. Les redireccions no se segueixen
        i poden requerir una revisió manual.
    </p>

</section>
{% endif %}

</main>

<footer>
    🛡️ ShopGuard · Eina de diagnòstic web
    <br><br>
    Una comprovació tècnica no és una garantia de seguretat.
</footer>

</body>
</html>
"""


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag.lower() == "a":
            href = attrs.get("href")
            if href:
                self.links.append(href)

        elif tag.lower() == "img":
            src = attrs.get("src")
            if src:
                self.images.append(src)


def is_public_url(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        # Només ports web habituals.
        port = parsed.port
        if port not in (None, 80, 443):
            return False

        host = parsed.hostname

        # No permetre dominis locals.
        if host.lower() == "localhost":
            return False

        addresses = socket.getaddrinfo(host, port or 443)

        ips = {item[4][0] for item in addresses}

        return bool(ips) and all(
            ipaddress.ip_address(ip.split("%")[0]).is_global
            for ip in ips
        )

    except (ValueError, OSError, socket.gaierror):
        return False


def fetch_url(url, read_html=False):
    if not is_public_url(url):
        return {
            "status": None,
            "body": "",
            "content_type": "",
            "message": "Adreça no pública o no permesa."
        }

    try:
        req = Request(
            url,
            headers={
                "User-Agent": "ShopGuard/1.0",
                "Accept": "text/html,*/*;q=0.8"
            }
        )

        with opener.open(req, timeout=TIMEOUT) as response:
            status = response.status
            content_type = response.headers.get(
                "Content-Type", ""
            )

            body = ""
            if read_html and "text/html" in content_type.lower():
                data = response.read(MAX_HTML_SIZE)
                body = data.decode("utf-8", errors="replace")

            return {
                "status": status,
                "body": body,
                "content_type": content_type,
                "message": f"HTTP {status}"
            }

    except HTTPError as exc:
        # Inclou errors HTTP i redireccions no seguides.
        return {
            "status": exc.code,
            "body": "",
            "content_type": "",
            "message": f"HTTP {exc.code}"
        }

    except (URLError, TimeoutError, OSError, ValueError):
        return {
            "status": None,
            "body": "",
            "content_type": "",
            "message": "No s'ha pogut completar la petició."
        }


def classify_result(result):
    status = result["status"]

    if status is None:
        return {
            "css": "bad",
            "symbol": "❌",
            "message": result["message"]
        }

    if 200 <= status < 300:
        return {
            "css": "ok",
            "symbol": "✅",
            "message": f"HTTP {status}: resposta correcta"
        }

    if 300 <= status < 400:
        return {
            "css": "warn",
            "symbol": "↪️",
            "message": f"HTTP {status}: redirecció no seguida"
        }

    return {
        "css": "bad",
        "symbol": "❌",
        "message": f"HTTP {status}: cal revisar-ho"
    }


def same_site_url(base_url, candidate):
    try:
        full_url = urljoin(base_url, candidate)
        base = urlparse(base_url)
        parsed = urlparse(full_url)

        # Només comprovem recursos del mateix host.
        if parsed.hostname != base.hostname:
            return None

        if parsed.scheme not in ("http", "https"):
            return None

        # Eliminar fragments: no s'envien al servidor.
        parsed = parsed._replace(fragment="")

        return parsed.geturl()

    except (ValueError, TypeError):
        return None


def unique_items(items):
    seen = set()
    result = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def analyze_website(url):
    homepage = fetch_url(url, read_html=True)
    home_result = classify_result(homepage)

    report = {
        "url": url,
        "home_status": (
            homepage["status"]
            if homepage["status"] is not None
            else "—"
        ),
        "home_message": home_result["message"],
        "home_class": home_result["css"],
        "links": [],
        "images": [],
        "links_checked": 0,
        "images_checked": 0
    }

    # Sense HTML no podem extreure recursos.
    if not homepage["body"]:
        return report

    parser = PageParser()

    try:
        parser.feed(homepage["body"])
    except Exception:
        return report

    links = unique_items([
        same_site_url(url, item)
        for item in parser.links
    ])
    links = [item for item in links if item][:MAX_LINKS]

    images = unique_items([
        same_site_url(url, item)
        for item in parser.images
    ])
    images = [item for item in images if item][:MAX_IMAGES]

    for link in links:
        result = fetch_url(link)
        classification = classify_result(result)

        report["links"].append({
            "url": link,
            **classification
        })

    for img in images:
        result = fetch_url(img)
        classification = classify_result(result)

        report["images"].append({
            "url": img,
            **classification
        })

    report["links_checked"] = len(report["links"])
    report["images_checked"] = len(report["images"])

    return report


@app.route("/", methods=["GET", "POST"])
def home():
    website = ""
    report = None
    error = None

    if request.method == "POST":
        website = request.form.get("website", "").strip()

        if not website:
            error = "Introdueix una adreça web."

        else:
            if "://" not in website:
                website = "https://" + website

            parsed = urlparse(website)

            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.port not in (None, 80, 443)
            ):
                error = (
                    "Introdueix una adreça HTTP o HTTPS vàlida "
                    "amb un port web habitual."
                )

            elif not is_public_url(website):
                error = (
                    "No s'ha pogut verificar una adreça web "
                    "pública. Comprova el domini i torna-ho a provar."
                )

            else:
                report = analyze_website(website)

    return render_template_string(
        PAGE,
        website=website,
        report=report,
        error=error
    )


if __name__ == "__main__":
    app.run()
