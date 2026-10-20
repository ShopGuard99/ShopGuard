from flask import Flask, request, render_template_string
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import socket
import ipaddress

app = Flask(__name__)

PAGE = """
<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ShopGuard</title>
<style>
body {
    background: #101522;
    color: white;
    font-family: Arial, sans-serif;
    margin: 0;
}
main {
    max-width: 720px;
    margin: 60px auto;
    padding: 24px;
}
h1 { font-size: 42px; }
h1 span { color: #59e3ad; }
p { color: #bdc6d8; line-height: 1.6; }
form { display: flex; gap: 10px; margin-top: 25px; }
input {
    flex: 1;
    min-width: 0;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid #38445b;
    background: #1a2233;
    color: white;
}
button {
    padding: 14px;
    border: 0;
    border-radius: 8px;
    background: #59e3ad;
    font-weight: bold;
    cursor: pointer;
}
.result {
    margin-top: 25px;
    padding: 20px;
    border-radius: 10px;
    background: #1a2233;
    overflow-wrap: anywhere;
}
@media(max-width: 550px) {
    form { flex-direction: column; }
}
</style>
</head>
<body>
<main>
<h1>🛡️ Shop<span>Guard</span></h1>
<p>Comprova si una web pública respon a una petició HTTP.</p>

<form method="post">
<input name="website" placeholder="example.com"
       value="{{ website }}" required>
<button type="submit">Analitzar web</button>
</form>

{% if results %}
<div class="result">
<h2>Resultats</h2>
<p><b>Adreça:</b> {{ website }}</p>
{% for result in results %}
<p>{{ result }}</p>
{% endfor %}
</div>
{% endif %}
</main>
</body>
</html>
"""

def resolve_public_host(host):
    try:
        addresses = socket.getaddrinfo(host, None)
        ips = {item[4][0] for item in addresses}
        return bool(ips) and all(
            ipaddress.ip_address(ip).is_global for ip in ips
        )
    except (socket.gaierror, ValueError, OSError):
        return False

@app.route("/", methods=["GET", "POST"])
def home():
    website = ""
    results = []

    if request.method == "POST":
        website = request.form.get("website", "").strip()

        if "://" not in website:
            website = "https://" + website

        parsed = urlparse(website)
        host = parsed.hostname

        if (
            parsed.scheme not in ("http", "https")
            or not host
            or "." not in host
            or parsed.username
            or parsed.password
        ):
            results.append("Introdueix una adreça web vàlida.")
        elif not resolve_public_host(host):
            results.append(
                "No s'ha pogut verificar un domini públic."
            )
        else:
            try:
                request_obj = Request(
                    website,
                    headers={"User-Agent": "ShopGuard/0.1"}
                )
                with urlopen(request_obj, timeout=8) as response:
                    results.append(
                        f"Resposta HTTP: {response.status}"
                    )
                    results.append(
                        "La web ha respost a la petició."
                    )
            except HTTPError as error:
                results.append(
                    f"La web ha retornat l'estat HTTP {error.code}."
                )
            except (URLError, TimeoutError, OSError):
                results.append(
                    "No s'ha pogut completar la petició HTTP. "
                    "La connexió pot estar bloquejada o la web "
                    "pot no respondre."
                )

    return render_template_string(
        PAGE, website=website, results=results
    )

if __name__ == "__main__":
    app.run()
