#!/usr/bin/env python3
"""Gera tráfego legítimo e/ou requisições 404 para validar a Stack ELK.

Exemplos:
  python3 scripts/gerar_trafego.py --normal-only --count 30
  python3 scripts/gerar_trafego.py --attack-only --count 250 --delay 0.01
  python3 scripts/gerar_trafego.py --count 30 --not-found 250
"""

from __future__ import annotations

import argparse
import time
from collections import Counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NORMAL_PATHS = ["/", "/sobre", "/api/status", "/health", "/arquivos/LEIA-ME.txt"]


def request_status(url: str, timeout: float = 5.0) -> int:
    request = Request(
        url,
        headers={"User-Agent": "StackELK-Pratica03-Test/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status
    except HTTPError as exc:
        return exc.code
    except URLError as exc:
        raise RuntimeError(f"Não foi possível acessar {url}: {exc.reason}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--count", type=int, default=30,
                        help="Quantidade de requisições legítimas ou 404 (padrão: 30).")
    parser.add_argument("--not-found", type=int, default=250,
                        help="Quantidade de páginas inexistentes (padrão: 250).")
    parser.add_argument("--delay", type=float, default=0.01,
                        help="Intervalo em segundos entre as requisições 404.")
    parser.add_argument("--normal-only", action="store_true")
    parser.add_argument("--attack-only", action="store_true")
    args = parser.parse_args()

    if args.count < 0 or args.not_found < 0 or args.delay < 0:
        parser.error("count, not-found e delay devem ser não negativos.")
    if args.normal_only and args.attack_only:
        parser.error("Use --normal-only ou --attack-only, não ambos.")

    base_url = args.base_url.rstrip("/")
    totals: Counter[int] = Counter()

    run_normal = not args.attack_only
    run_attack = not args.normal_only

    if run_normal:
        print(f"[NORMAL] Gerando {args.count} requisições legítimas...")
        for index in range(args.count):
            path = NORMAL_PATHS[index % len(NORMAL_PATHS)]
            status = request_status(f"{base_url}{path}")
            totals[status] += 1
            print(f"  {status} GET {path}")

    if run_attack:
        print(f"[TESTE 404] Gerando {args.not_found} requisições a arquivos inexistentes...")
        for index in range(1, args.not_found + 1):
            path = f"/arquivos/inexistentes/recurso-{index:04d}.txt"
            status = request_status(f"{base_url}{path}")
            totals[status] += 1
            if index <= 5 or index == args.not_found:
                print(f"  {status} GET {path}")
            elif index == 6:
                print("  ...")
            if args.delay:
                time.sleep(args.delay)

    print("\nResumo das respostas HTTP:")
    for status, amount in sorted(totals.items()):
        print(f"  HTTP {status}: {amount}")
    print("\nAguarde alguns segundos para o Filebeat encaminhar os eventos ao Elasticsearch.")
    print("No Kibana, filtre: event.dataset : \"nginx.access\" and http.response.status_code : 404")


if __name__ == "__main__":
    main()
