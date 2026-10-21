from flask import Flask, request, render_template_string
from urllib.parse import urlparse, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from time import perf_counter
import socket
import ipaddress

app = Flask(__name__)

MAX_LINKS = 10
MAX_IMAGES = 10
TIMEOUT = 5
MAX_HTML_SIZE = 1_000_000


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = build_opener(NoRedirectHandler())


PAGE = r"""
<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b1020">
<meta name="description" content="Comprova l'estat HTTP, els enllaços i les imatges de la teva web amb ShopGuard.">
<title>ShopGuard — Web Health Checker</title>
<style>
:root{color-scheme:dark;--bg:#080d19;--panel:#111a2c;--panel2:#17233a;--green:#63f0b5;--text:#f3f6ff;--muted:#a7b4cc;--border:#293750;--red:#ff8491;--yellow:#ffd47c;--blue:#9db9ff}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 50% -10%,#1c3652 0%,var(--bg) 58%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:5;background:#080d19eF;border-bottom:1px solid var(--border);backdrop-filter:blur(14px)}
nav{max-width:1120px;margin:auto;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;gap:16px}
.logo{font-size:23px;font-weight:900;letter-spacing:-1px;white-space:nowrap}.logo span{color:var(--green)}
.nav-right{display:flex;align-items:center;gap:12px}
.pill{font-size:10px;letter-spacing:1.4px;font-weight:800;color:var(--green);border:1px solid #326b5c;border-radius:30px;padding:8px 11px}
select{background:var(--panel2);color:var(--text);border:1px solid var(--border);padding:10px 12px;border-radius:10px;font:inherit;font-size:13px;cursor:pointer;max-width:100%}
main{max-width:1060px;padding:62px 22px 70px;margin:auto}
.hero{text-align:center;margin-bottom:42px}
.eyebrow{color:var(--green);text-transform:uppercase;font-size:11px;letter-spacing:2px;font-weight:850}
h1{font-size:clamp(38px,7vw,68px);letter-spacing:-2.8px;line-height:1.02;margin:18px 0}
h1 span{color:var(--green)}
.hero>p{max-width:650px;margin:0 auto;color:var(--muted);line-height:1.8;font-size:16px}
.scanner{max-width:790px;margin:32px auto 0;padding:9px;display:flex;gap:10px;background:#111a2cf2;border:1px solid #34435e;border-radius:17px;box-shadow:0 22px 75px #0005}
input{flex:1;min-width:0;padding:17px 15px;color:white;background:transparent;border:0;outline:none;font-size:15px}
input::placeholder{color:#7e8ba5}
button{background:var(--green);color:#071a14;border:0;padding:0 22px;border-radius:11px;font-weight:850;font-size:14px;cursor:pointer;transition:transform .15s,filter .15s}
button:hover{filter:brightness(1.08);transform:translateY(-1px)}button:disabled{opacity:.65;cursor:wait;transform:none}
.hint{color:var(--muted);font-size:12px;margin-top:13px}
.loading{display:none;margin:20px auto;color:var(--green);font-size:13px}
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:48px}
.card,.section,.stat{background:linear-gradient(145deg,var(--panel),#0e1626);border:1px solid var(--border);border-radius:17px}
.card{padding:23px;transition:transform .2s,border-color .2s}.card:hover{transform:translateY(-3px);border-color:#46637a}
.icon{font-size:27px}.card h3{margin:14px 0 8px;font-size:17px}.card p{color:var(--muted);line-height:1.7;font-size:13px;margin:0}
.results{margin-top:42px;scroll-margin-top:90px}.results h2{font-size:28px;letter-spacing:-.7px;margin-bottom:8px}
.url{color:var(--blue);overflow-wrap:anywhere;font-size:13px}
.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}
.stat{padding:19px}.stat strong{display:block;font-size:27px;margin-bottom:5px}.stat span{color:var(--muted);font-size:12px}
.section{margin-top:16px;padding:22px}.section h3{margin:0 0 12px;font-size:17px}
.row{padding:13px 0;border-bottom:1px solid var(--border);overflow-wrap:anywhere;line-height:1.65;font-size:13px}.row:last-child{border-bottom:0}
.ok{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--yellow)}
.notice{color:var(--muted);font-size:12px;line-height:1.7;margin-top:18px}
.errorbox{margin:25px auto 0;max-width:790px;padding:17px 20px;border:1px solid #79434a;border-radius:13px;background:#321b25;color:#ffdbe0;text-align:left}
footer{text-align:center;padding:28px 20px;border-top:1px solid var(--border);color:var(--muted);font-size:12px;line-height:1.8}
footer strong{color:var(--text)}
@media(max-width:720px){main{padding-top:42px}.features{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,1fr)}nav{padding:13px 15px}.pill{display:none}}
@media(max-width:520px){.nav-right{gap:7px}select{padding:9px 8px;max-width:140px}.logo{font-size:20px}h1{letter-spacing:-1.5px}.hero>p{font-size:14px}.scanner{flex-direction:column}input{padding:15px 12px}button{padding:16px}.summary{grid-template-columns:1fr 1fr}.stat{padding:15px}.stat strong{font-size:23px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>
</head>
<body>
<header><nav>
  <div class="logo">🛡️ Shop<span>Guard</span></div>
  <div class="nav-right">
    <div class="pill">WEB HEALTH CHECKER</div>
    <label for="language" class="sr-only" style="position:absolute;left:-9999px">Language</label>
    <select id="language" aria-label="Choose language">
      <option value="ca">🇨🇦 Català</option>
      <option value="es">🇪🇸 Español</option>
      <option value="en">🇬🇧 English</option>
      <option value="fr">🇫🇷 Français</option>
    </select>
  </div>
</nav></header>
<main>
<section class="hero">
  <div class="eyebrow" data-i18n="eyebrow">Diagnòstic web simplificat</div>
  <h1 data-i18n="title">La salut de la teva web,<br><span>d'un cop d'ull.</span></h1>
  <p data-i18n="intro">Comprova l'estat HTTP de la teva pàgina i detecta enllaços i imatges que poden donar problemes. Resultats senzills, sense complicacions.</p>
  <form class="scanner" method="post" id="scan-form">
    <input type="text" name="website" id="website" placeholder="https://elteudomini.com" value="{{ website }}" aria-label="Website address" required autocomplete="url" spellcheck="false">
    <button type="submit" id="scan-button" data-i18n="button">🔍 Analitzar web</button>
  </form>
  <div class="hint" data-i18n="hint">Analitza només webs públiques que tinguis permís per comprovar.</div>
  <div class="loading" id="loading" data-i18n="loading">⏳ Analitzant la web… pot trigar uns segons.</div>
  {% if error %}<div class="errorbox"><strong data-i18n="errorTitle">⚠️ No s'ha pogut analitzar</strong><p>{{ error }}</p></div>{% endif %}
</section>
<section class="features">
  <article class="card"><div class="icon">🌐</div><h3 data-i18n="feature1Title">Estat de la web</h3><p data-i18n="feature1Text">Comprova si el servidor respon i mostra el codi HTTP retornat per la pàgina.</p></article>
  <article class="card"><div class="icon">🔗</div><h3 data-i18n="feature2Title">Enllaços interns</h3><p data-i18n="feature2Text">Revisa fins a 10 enllaços interns per trobar pàgines que retornin errors.</p></article>
  <article class="card"><div class="icon">🖼️</div><h3 data-i18n="feature3Title">Imatges</h3><p data-i18n="feature3Text">Comprova fins a 10 imatges de la mateixa web per detectar recursos que fallen.</p></article>
</section>
{% if report %}
<section class="results" id="results">
  <h2 data-i18n="reportTitle">📊 Informe de l'anàlisi</h2>
  <p class="url">{{ report.url }}</p>
  <div class="summary">
    <div class="stat"><strong class="{{ report.home_class }}">{{ report.home_status }}</strong><span data-i18n="statHttp">Estat HTTP</span></div>
    <div class="stat"><strong>{{ report.links_checked }}</strong><span data-i18n="statLinks">Enllaços comprovats</span></div>
    <div class="stat"><strong>{{ report.images_checked }}</strong><span data-i18n="statImages">Imatges comprovades</span></div>
    <div class="stat"><strong>{{ report.elapsed }} s</strong><span data-i18n="statTime">Temps d'anàlisi del servidor</span></div>
  </div>
  <div class="section"><h3 data-i18n="homeResult">🌐 Resultat de la pàgina</h3><p class="{{ report.home_class }}">{{ report.home_message }}</p></div>
  <div class="section"><h3 data-i18n="linksTitle">🔗 Enllaços interns</h3>
    {% if report.links %}{% for item in report.links %}<div class="row"><span class="{{ item.css }}">{{ item.symbol }} {{ item.message }}</span><br><span class="url">{{ item.url }}</span></div>{% endfor %}
    {% else %}<p data-i18n="noLinks">No s'han trobat enllaços interns per comprovar.</p>{% endif %}
  </div>
  <div class="section"><h3 data-i18n="imagesTitle">🖼️ Imatges</h3>
    {% if report.images %}{% for item in report.images %}<div class="row"><span class="{{ item.css }}">{{ item.symbol }} {{ item.message }}</span><br><span class="url">{{ item.url }}</span></div>{% endfor %}
    {% else %}<p data-i18n="noImages">No s'han trobat imatges internes per comprovar.</p>{% endif %}
  </div>
  <div class="section"><h3 data-i18n="historyTitle">🕘 Historial recent (aquest navegador)</h3><div id="history-list" class="row" data-i18n="historyEmpty">Les webs que analitzis apareixeran aquí.</div><button type="button" id="clear-history" style="padding:12px 15px;margin-top:12px" data-i18n="clearHistory">Esborrar historial</button></div>
  <p class="notice" data-i18n="notice">Aquesta és una comprovació limitada, no una auditoria de seguretat. Només es revisen fins a 10 enllaços i 10 imatges del mateix domini. Alguns servidors bloquegen les comprovacions automàtiques i les redireccions no se segueixen.</p>
</section>
{% endif %}
</main>
<footer><strong>🛡️ ShopGuard</strong> · <span data-i18n="footer">Eina de diagnòstic web</span><br><span data-i18n="footerNote">Una comprovació tècnica no és una garantia de seguretat.</span></footer>
<script>
const translations = {
ca: {
eyebrow:"Diagnòstic web simplificat", title:"La salut de la teva web,<br><span>d'un cop d'ull.</span>",
intro:"Comprova l'estat HTTP de la teva pàgina i detecta enllaços i imatges que poden donar problemes. Resultats senzills, sense complicacions.",
button:"🔍 Analitzar web", hint:"Analitza només webs públiques que tinguis permís per comprovar.", loading:"⏳ Analitzant la web… pot trigar uns segons.",
errorTitle:"⚠️ No s'ha pogut analitzar", feature1Title:"Estat de la web", feature1Text:"Comprova si el servidor respon i mostra el codi HTTP retornat per la pàgina.",
feature2Title:"Enllaços interns", feature2Text:"Revisa fins a 10 enllaços interns per trobar pàgines que retornin errors.", feature3Title:"Imatges",
feature3Text:"Comprova fins a 10 imatges de la mateixa web per detectar recursos que fallen.", reportTitle:"📊 Informe de l'anàlisi",
statHttp:"Estat HTTP", statLinks:"Enllaços comprovats", statImages:"Imatges comprovades", statTime:"Temps d'anàlisi del servidor",
homeResult:"🌐 Resultat de la pàgina", linksTitle:"🔗 Enllaços interns", imagesTitle:"🖼️ Imatges",
noLinks:"No s'han trobat enllaços interns per comprovar.", noImages:"No s'han trobat imatges internes per comprovar.",
historyTitle:"🕘 Historial recent (aquest navegador)", historyEmpty:"Les webs que analitzis apareixeran aquí.", clearHistory:"Esborrar historial",
notice:"Aquesta és una comprovació limitada, no una auditoria de seguretat. Només es revisen fins a 10 enllaços i 10 imatges del mateix domini. Alguns servidors bloquegen les comprovacions automàtiques i les redireccions no se segueixen.",
footer:"Eina de diagnòstic web", footerNote:"Una comprovació tècnica no és una garantia de seguretat."
},
es: {
eyebrow:"Diagnóstico web simplificado", title:"La salud de tu web,<br><span>de un vistazo.</span>",
intro:"Comprueba el estado HTTP de tu página y detecta enlaces e imágenes que pueden dar problemas. Resultados sencillos, sin complicaciones.",
button:"🔍 Analizar web", hint:"Analiza solo sitios públicos que tengas permiso para comprobar.", loading:"⏳ Analizando la web… puede tardar unos segundos.",
errorTitle:"⚠️ No se ha podido analizar", feature1Title:"Estado de la web", feature1Text:"Comprueba si el servidor responde y muestra el código HTTP de la página.",
feature2Title:"Enlaces internos", feature2Text:"Revisa hasta 10 enlaces internos para encontrar páginas con errores.", feature3Title:"Imágenes",
feature3Text:"Comprueba hasta 10 imágenes del mismo sitio para detectar recursos que fallan.", reportTitle:"📊 Informe del análisis",
statHttp:"Estado HTTP", statLinks:"Enlaces comprobados", statImages:"Imágenes comprobadas", statTime:"Tiempo de análisis del servidor",
homeResult:"🌐 Resultado de la página", linksTitle:"🔗 Enlaces internos", imagesTitle:"🖼️ Imágenes",
noLinks:"No se han encontrado enlaces internos para comprobar.", noImages:"No se han encontrado imágenes internas para comprobar.",
historyTitle:"🕘 Historial reciente (este navegador)", historyEmpty:"Los sitios que analices aparecerán aquí.", clearHistory:"Borrar historial",
notice:"Esta es una comprobación limitada, no una auditoría de seguridad. Solo se revisan hasta 10 enlaces y 10 imágenes del mismo dominio. Algunos servidores bloquean las comprobaciones automáticas y no se siguen las redirecciones.",
footer:"Herramienta de diagnóstico web", footerNote:"Una comprobación técnica no garantiza la seguridad."
},
en: {
eyebrow:"Web diagnostics made simple", title:"Your website's health,<br><span>at a glance.</span>",
intro:"Check your page's HTTP status and find links and images that may be broken. Clear results, without the complexity.",
button:"🔍 Scan website", hint:"Only scan public websites you have permission to test.", loading:"⏳ Scanning website… this may take a few seconds.",
errorTitle:"⚠️ Could not scan", feature1Title:"Website status", feature1Text:"Check whether the server responds and view the page's HTTP status code.",
feature2Title:"Internal links", feature2Text:"Check up to 10 internal links to find pages returning errors.", feature3Title:"Images",
feature3Text:"Check up to 10 images on the same website to find resources that fail.", reportTitle:"📊 Scan report",
statHttp:"HTTP status", statLinks:"Links checked", statImages:"Images checked", statTime:"Server scan time",
homeResult:"🌐 Page result", linksTitle:"🔗 Internal links", imagesTitle:"🖼️ Images",
noLinks:"No internal links were found to check.", noImages:"No internal images were found to check.",
historyTitle:"🕘 Recent history (this browser)", historyEmpty:"Websites you scan will appear here.", clearHistory:"Clear history",
notice:"This is a limited check, not a security audit. Only up to 10 links and 10 images on the same domain are checked. Some servers block automated checks, and redirects are not followed.",
footer:"Web diagnostic tool", footerNote:"A technical check is not a guarantee of security."
},
fr: {
eyebrow:"Diagnostic web simplifié", title:"La santé de votre site,<br><span>en un coup d’œil.</span>",
intro:"Vérifiez le statut HTTP de votre page et repérez les liens et images susceptibles de poser problème. Des résultats simples, sans complication.",
button:"🔍 Analyser le site", hint:"Analysez uniquement les sites publics que vous êtes autorisé à vérifier.", loading:"⏳ Analyse du site… cela peut prendre quelques secondes.",
errorTitle:"⚠️ Analyse impossible", feature1Title:"État du site", feature1Text:"Vérifiez si le serveur répond et consultez le code HTTP de la page.",
feature2Title:"Liens internes", feature2Text:"Vérifiez jusqu’à 10 liens internes pour repérer les pages en erreur.", feature3Title:"Images",
feature3Text:"Vérifiez jusqu’à 10 images du même site pour repérer les ressources défaillantes.", reportTitle:"📊 Rapport d’analyse",
statHttp:"Statut HTTP", statLinks:"Liens vérifiés", statImages:"Images vérifiées", statTime:"Durée de l’analyse serveur",
homeResult:"🌐 Résultat de la page", linksTitle:"🔗 Liens internes", imagesTitle:"🖼️ Images",
noLinks:"Aucun lien interne à vérifier n’a été trouvé.", noImages:"Aucune image interne à vérifier n’a été trouvée.",
historyTitle:"🕘 Historique récent (ce navigateur)", historyEmpty:"Les sites analysés apparaîtront ici.", clearHistory:"Effacer l’historique",
notice:"Cette vérification est limitée et ne constitue pas un audit de sécurité. Jusqu’à 10 liens et 10 images du même domaine sont vérifiés. Certains serveurs bloquent les vérifications automatiques et les redirections ne sont pas suivies.",
footer:"Outil de diagnostic web", footerNote:"Une vérification technique ne garantit pas la sécurité."
}
};
const langSelect = document.getElementById("language");
function setLanguage(lang) {
  const dict = translations[lang] || translations.ca;
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.innerHTML = dict[key];
  });
  const input = document.getElementById("website");
  input.placeholder = lang === "es" ? "https://tudominio.com" :
    lang === "en" ? "https://yourdomain.com" :
    lang === "fr" ? "https://votredomaine.fr" : "https://elteudomini.com";
  localStorage.setItem("shopguard-language", lang);
}
const savedLang = localStorage.getItem("shopguard-language") || "ca";
langSelect.value = savedLang;
setLanguage(savedLang);
langSelect.addEventListener("change", () => setLanguage(langSelect.value));

const form = document.getElementById("scan-form");
form.addEventListener("submit", () => {
  document.getElementById("scan-button").disabled = true;
  document.getElementById("loading").style.display = "block";
});
const historyKey = "shopguard-history-v1";
function renderHistory() {
  const target = document.getElementById("history-list");
  if (!target) return;
  let entries = [];
  try { entries = JSON.parse(localStorage.getItem(historyKey) || "[]"); } catch (_) {}
  if (!entries.length) {
    target.textContent = translations[langSelect.value].historyEmpty;
    return;
  }
  target.innerHTML = "";
  entries.forEach(entry => {
    const row = document.createElement("div");
    row.className = "row";
    const link = document.createElement("a");
    link.href = entry.url; link.textContent = entry.url; link.className = "url";
    link.rel = "noopener noreferrer"; link.target = "_blank";
    const meta = document.createElement("div");
    meta.textContent = entry.status + " · " + entry.date;
    row.append(link, meta); target.appendChild(row);
  });
}
const clearButton = document.getElementById("clear-history");
if (clearButton) clearButton.addEventListener("click", () => {
  localStorage.removeItem(historyKey); renderHistory();
});
{% if report %}
try {
  const entries = JSON.parse(localStorage.getItem(historyKey) || "[]");
  entries.unshift({url: {{ report.url|tojson }}, status: {{ report.home_status|string|tojson }}, date: new Date().toLocaleString()});
  localStorage.setItem(historyKey, JSON.stringify(entries.slice(0, 8)));
} catch (_) {}
const results = document.getElementById("results");
if (results) setTimeout(() => results.scrollIntoView({behavior:"smooth",block:"start"}), 80);
{% endif %}
renderHistory();
</script>
</body></html>
"""


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag.lower() == "img" and attrs.get("src"):
            self.images.append(attrs["src"])


def is_public_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        if parsed.username or parsed.password:
            return False
        port = parsed.port
        if port not in (None, 80, 443):
            return False
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return False
        infos = socket.getaddrinfo(host, port or (443 if parsed.scheme == "https" else 80))
        ips = {item[4][0] for item in infos}
        return bool(ips) and all(
            ipaddress.ip_address(ip.split("%")[0]).is_global for ip in ips
        )
    except (ValueError, OSError, socket.gaierror):
        return False


def fetch_url(url, read_html=False):
    if not is_public_url(url):
        return {"status": None, "body": "", "content_type": "",
                "message": "Adreça no pública o no permesa."}
    try:
        req = Request(url, headers={
            "User-Agent": "ShopGuard/2.0 (+website health checker)",
            "Accept": "text/html,*/*;q=0.8"
        })
        with opener.open(req, timeout=TIMEOUT) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            body = ""
            if read_html and "text/html" in content_type.lower():
                body = response.read(MAX_HTML_SIZE).decode("utf-8", errors="replace")
            return {"status": status, "body": body, "content_type": content_type,
                    "message": f"HTTP {status}"}
    except HTTPError as exc:
        return {"status": exc.code, "body": "", "content_type": "",
                "message": f"HTTP {exc.code}"}
    except (URLError, TimeoutError, OSError, ValueError):
        return {"status": None, "body": "", "content_type": "",
                "message": "No s'ha pogut completar la petició."}


def classify_result(result):
    status = result["status"]
    if status is None:
        return {"css": "bad", "symbol": "❌", "message": result["message"]}
    if 200 <= status < 300:
        return {"css": "ok", "symbol": "✅", "message": f"HTTP {status}: resposta correcta"}
    if 300 <= status < 400:
        return {"css": "warn", "symbol": "↪️", "message": f"HTTP {status}: redirecció no seguida"}
    return {"css": "bad", "symbol": "❌", "message": f"HTTP {status}: cal revisar-ho"}


def same_site_url(base_url, candidate):
    try:
        full_url = urljoin(base_url, candidate)
        base = urlparse(base_url)
        parsed = urlparse(full_url)
        if parsed.hostname != base.hostname or parsed.scheme not in ("http", "https"):
            return None
        parsed = parsed._replace(fragment="")
        return parsed.geturl()
    except (ValueError, TypeError):
        return None


def unique_items(items):
    seen, result = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def analyze_website(url):
    started = perf_counter()
    homepage = fetch_url(url, read_html=True)
    home_result = classify_result(homepage)
    report = {
        "url": url,
        "home_status": homepage["status"] if homepage["status"] is not None else "—",
        "home_message": home_result["message"],
        "home_class": home_result["css"],
        "links": [], "images": [], "links_checked": 0, "images_checked": 0,
        "elapsed": "0.00"
    }
    if homepage["body"]:
        parser = PageParser()
        try:
            parser.feed(homepage["body"])
        except Exception:
            parser = PageParser()
        links = unique_items([same_site_url(url, item) for item in parser.links])
        images = unique_items([same_site_url(url, item) for item in parser.images])
        links = [item for item in links if item][:MAX_LINKS]
        images = [item for item in images if item][:MAX_IMAGES]
        for link in links:
            report["links"].append({"url": link, **classify_result(fetch_url(link))})
        for img in images:
            report["images"].append({"url": img, **classify_result(fetch_url(img))})
    report["links_checked"] = len(report["links"])
    report["images_checked"] = len(report["images"])
    report["elapsed"] = f"{perf_counter() - started:.2f}"
    return report


@app.route("/", methods=["GET", "POST"])
def home():
    website, report, error = "", None, None
    if request.method == "POST":
        website = request.form.get("website", "").strip()
        if not website:
            error = "Introdueix una adreça web."
        else:
            if "://" not in website:
                website = "https://" + website
            parsed = urlparse(website)
            try:
                valid_port = parsed.port in (None, 80, 443)
            except ValueError:
                valid_port = False
            if (parsed.scheme not in ("http", "https") or not parsed.hostname
                    or parsed.username or parsed.password or not valid_port):
                error = "Introdueix una adreça HTTP o HTTPS vàlida amb un port web habitual."
            elif not is_public_url(website):
                error = "No s'ha pogut verificar una adreça web pública. Comprova el domini i torna-ho a provar."
            else:
                report = analyze_website(website)
    return render_template_string(PAGE, website=website, report=report, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port= int(__import__("os").environ.get("PORT", "5000")))
