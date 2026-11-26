# APRESENTACAO: servidor HTTP local | http.server | navegador <-> Python
# Entrega HTML/CSS/JS; recebe o codigo e encaminha ao service.py.

"""Painel local: python gui.py. Não depende de pacotes externos nem executa Python do editor."""
import argparse
import json
# http.server fornece o servidor HTTP da biblioteca padrão; não há framework web.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser
from parkingdsl.service import run_source

ROOT = Path(__file__).resolve().parent
# Lista fechada de arquivos servidos: evita transformar URLs em caminhos arbitrários.
ASSETS = {'/': ('index.html', 'text/html'), '/app.css': ('app.css', 'text/css'),
          '/app.js': ('app.js', 'text/javascript')}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    # Envia JSON ou arquivo estático com tipo, tamanho e cabeçalhos de proteção.
    def reply(self, status, payload, content_type='application/json'):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    # Aceita apenas o endereço local esperado e origens do próprio painel.
    def allowed(self):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        origin = self.headers.get('Origin')
        return self.headers.get('Host') in hosts and (not origin or origin in {f'http://{h}' for h in hosts})

    # GET carrega a interface e os exemplos disponíveis; não executa programas.
    def do_GET(self):
        if not self.allowed():
            return self.reply(403, {'error': 'Acesso permitido somente pelo endereço local.'})
        if self.path == '/api/examples':
            return self.reply(200, [dict(name=p.stem, source=p.read_text(encoding='utf-8'))
                                    for p in sorted((ROOT / 'examples').glob('*.dsl'))])
        if self.path in ASSETS:
            name, kind = ASSETS[self.path]
            return self.reply(200, (ROOT / 'web' / name).read_bytes(), kind)
        return self.reply(404, {'error': 'Recurso não encontrado.'})

    # POST /api/run recebe o texto em JSON, valida limites e chama o núcleo Python.
    def do_POST(self):
        if not self.allowed():
            return self.reply(403, {'error': 'Origem não permitida.'})
        if self.path != '/api/run':
            return self.reply(404, {'error': 'Recurso não encontrado.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 400000:
                return self.reply(413, {'error': 'Arquivo muito grande ou requisição vazia.'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'Envie JSON.'})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Requisição inválida.')
            result = run_source(payload.get('source'))
        except (ValueError, UnicodeError) as exc:
            return self.reply(400, {'error': str(exc)})
        return self.reply(200, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        # Loopback restringe o servidor a este computador. O estado de cada execução é separado.
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as exc:
        parser.exit(1, f'Não foi possível iniciar: {exc}. Tente --port 8766.\n')
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'EstacionaDSL Studio: {url}\nMantenha este terminal aberto. Ctrl+C encerra o painel.', flush=True)
    # Abre o navegador por conveniência. O terminal precisa continuar ativo para atender a página.
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
