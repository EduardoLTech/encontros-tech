#!/usr/bin/env python3
"""Popula a aplicacao Encontros Tech com eventos de exemplo via chamadas HTTP a API.

Uso:
    python scripts/seed.py [--base-url http://localhost:8000]
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urlencode

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

EVENTS = [
    {
        "title": "Workshop: Introdução ao FastAPI",
        "description": "Aprenda a criar APIs REST modernas com FastAPI, incluindo documentação automática, validação de dados e deploy em produção.",
        "date": "2024-02-15T19:00:00",
        "location": "Centro de Convenções - São Paulo, SP",
        "technologies": ["Python", "FastAPI", "REST API", "Swagger"],
    },
    {
        "title": "Meetup React: Performance com Next.js 14",
        "description": "Discussão sobre otimização de performance em aplicações React usando as novas funcionalidades do Next.js 14.",
        "date": "2024-02-20T18:30:00",
        "location": "Hub de Inovação - Rio de Janeiro, RJ",
        "technologies": ["JavaScript", "React", "Next.js", "Frontend"],
    },
    {
        "title": "DevOps Conference 2024: Kubernetes na Prática",
        "description": "Evento focado em práticas DevOps modernas, com palestras sobre Kubernetes, CI/CD, monitoramento e observabilidade.",
        "date": "2024-03-05T09:00:00",
        "location": "Expo Center Norte - São Paulo, SP",
        "technologies": ["Kubernetes", "Docker", "CI/CD", "DevOps", "Prometheus", "Grafana"],
    },
    {
        "title": "Hackathon Mobile: Apps para Sustentabilidade",
        "description": "48 horas de desenvolvimento intensivo para criar aplicativos móveis que promovam sustentabilidade e consciência ambiental.",
        "date": "2024-02-25T08:00:00",
        "location": "Campus Universitário - Belo Horizonte, MG",
        "technologies": ["React Native", "Flutter", "Mobile", "Sustainability"],
    },
    {
        "title": "IA na Prática: Machine Learning com Python",
        "description": "Como implementar soluções de Machine Learning em produção usando Python, scikit-learn e TensorFlow.",
        "date": "2024-03-10T14:00:00",
        "location": "Auditório Tech Hub - Brasília, DF",
        "technologies": ["Python", "Machine Learning", "TensorFlow", "Scikit-learn", "AI"],
    },
    {
        "title": "AWS na Prática: Serverless com Lambda",
        "description": "Workshop hands-on sobre desenvolvimento serverless na AWS usando Lambda, API Gateway e DynamoDB.",
        "date": "2024-03-15T10:00:00",
        "location": "Centro de Treinamento - Porto Alegre, RS",
        "technologies": ["AWS", "Lambda", "Serverless", "DynamoDB", "Cloud"],
    },
    {
        "title": "PostgreSQL Avançado: Otimização e Performance",
        "description": "Técnicas avançadas de otimização em PostgreSQL, incluindo índices, particionamento e análise de performance.",
        "date": "2024-02-28T19:30:00",
        "location": "Coworking Space - Florianópolis, SC",
        "technologies": ["PostgreSQL", "Database", "SQL", "Performance"],
    },
    {
        "title": "Cybersecurity Summit: Proteção de APIs",
        "description": "Estratégias para proteger APIs REST contra ataques comuns, incluindo autenticação, autorização e monitoramento.",
        "date": "2024-03-20T13:00:00",
        "location": "Centro Empresarial - Curitiba, PR",
        "technologies": ["Security", "API Security", "JWT", "OAuth", "Cybersecurity"],
    },
    {
        "title": "Modern Frontend: Vue.js 3 + TypeScript",
        "description": "Desenvolvimento de aplicações frontend modernas com Vue.js 3, Composition API e TypeScript.",
        "date": "2024-04-05T15:00:00",
        "location": "Innovation Lab - Salvador, BA",
        "technologies": ["Vue.js", "TypeScript", "Frontend", "JavaScript"],
    },
    {
        "title": "Blockchain & Web3: Desenvolvimento de DApps",
        "description": "Introdução ao desenvolvimento de aplicações descentralizadas (DApps) usando Solidity e frameworks Web3.",
        "date": "2024-04-10T11:00:00",
        "location": "Tech Park - Recife, PE",
        "technologies": ["Blockchain", "Solidity", "Web3", "DApps", "Ethereum"],
    },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Popula a aplicação Encontros Tech com eventos de exemplo via API HTTP."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL base da aplicação (default: http://localhost:8000)",
    )
    return parser.parse_args()


def request_json(method: str, url: str, payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            pass
        return e.code, body
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise ConnectionError(
            f"Não foi possível conectar à API em {url}. "
            f"Verifique se a aplicação está no ar e se --base-url está correto. Detalhe: {e}"
        ) from e


def get_existing_titles(base_url: str) -> set[str]:
    titles: set[str] = set()
    skip = 0
    limit = 100
    while True:
        query = urlencode({"skip": skip, "limit": limit})
        status, body = request_json("GET", f"{base_url}/api/events/?{query}")
        if status != 200:
            raise RuntimeError(f"Falha ao listar eventos existentes (status {status}): {body}")
        if not body:
            break
        titles.update(event["title"] for event in body)
        if len(body) < limit:
            break
        skip += limit
    return titles


def create_event(base_url: str, event: dict):
    status, body = request_json("POST", f"{base_url}/api/events/", event)
    if status not in (200, 201):
        raise RuntimeError(f"Falha ao criar evento '{event['title']}' (status {status}): {body}")
    return body


def main():
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        existing_titles = get_existing_titles(base_url)
    except ConnectionError as e:
        print(f"Erro de conexão: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Erro ao consultar a API: {e}", file=sys.stderr)
        sys.exit(1)

    created = 0
    skipped = 0

    for event in EVENTS:
        if event["title"] in existing_titles:
            print(f"[já existe] {event['title']}")
            skipped += 1
            continue

        try:
            create_event(base_url, event)
        except ConnectionError as e:
            print(f"Erro de conexão: {e}", file=sys.stderr)
            sys.exit(1)
        except RuntimeError as e:
            print(f"[erro] {event['title']}: {e}", file=sys.stderr)
            continue

        print(f"[criado]    {event['title']}")
        created += 1

    print()
    print(f"Eventos criados: {created}")
    print(f"Eventos já existentes: {skipped}")


if __name__ == "__main__":
    main()
