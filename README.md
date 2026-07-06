# Encontros Tech

## Visão geral

Encontros Tech é uma aplicação web para divulgação e gestão de eventos de tecnologia (workshops, meetups, hackathons etc.). A aplicação expõe:

- uma interface web (páginas de listagem, criação, edição e detalhe de eventos), servida pelo blueprint `page_router` ([src/routers/page_router.py](src/routers/page_router.py));
- uma API REST de eventos em `/api/events`, servida pelo blueprint `api_router` ([src/routers/api_router.py](src/routers/api_router.py));
- endpoints de saúde `/health` e `/ready` ([src/routers/health_router.py](src/routers/health_router.py)).

Edição de eventos é feita via `edit_token` (token retornado na criação), sem sistema de autenticação de usuários — não encontrei rotas de login/autenticação no repositório.

## Stack

Versões declaradas em [src/requirements.txt](src/requirements.txt) e no [src/Dockerfile](src/Dockerfile):

- Python 3.12 (imagem base `python:3.12-slim`, `src/Dockerfile:1`)
- Flask 3.0.0
- Gunicorn 21.2.0 (servidor WSGI de produção)
- SQLAlchemy 2.0.43 + psycopg2-binary 2.9.10 (ORM / driver PostgreSQL)
- Pydantic 2.11.7 / pydantic-settings 2.10.1 (configuração e validação)
- Jinja2 3.1.6 (templates HTML)
- prometheus-flask-exporter 0.23.0 / prometheus-client 0.21.1 (métricas)
- pytest 8.3.4 (testes)
- PostgreSQL 16 (imagem `postgres:16-alpine`, usada em [docker-compose.yml](docker-compose.yml) e [k8s/encontros-tech.yaml](k8s/encontros-tech.yaml))

Versão de Python para rodar fora do Docker (sem usar a imagem do Dockerfile): **A confirmar**.

## Pré-requisitos

- Docker e Docker Compose (para o caminho local via `docker-compose.yml`)
- Terraform >= 1.5.0, com provider `aws ~> 5.60` (declarado em [terraform/providers.tf](terraform/providers.tf)), para provisionar a infraestrutura
- Acesso a um cluster Kubernetes e `kubectl` configurado, para aplicar os manifests em [k8s/encontros-tech.yaml](k8s/encontros-tech.yaml)
- Credenciais AWS configuradas (o provider Terraform lê a região em `var.region`, default `us-east-1`, [terraform/variables.tf](terraform/variables.tf))

## Como rodar local

O caminho com origem confirmada no repositório é via Docker Compose ([docker-compose.yml](docker-compose.yml)):

1. Copie o arquivo de variáveis de ambiente de exemplo:
   ```
   cp .env.exemple .env
   ```
   (arquivo de exemplo em [.env.exemple](.env.exemple); há também [src/.env.example](src/.env.example) com o mesmo conteúdo mais `PROMETHEUS_MULTIPROC_DIR`)
2. Suba os serviços:
   ```
   docker compose up --build
   ```
   Isso builda a imagem a partir de `./src` usando o [src/Dockerfile](src/Dockerfile) e sobe:
   - serviço `app`: aplicação Flask, porta `8000:8000`
   - serviço `db`: PostgreSQL 16-alpine, porta `5432:5432`, com healthcheck `pg_isready`
3. A aplicação estará disponível em `http://localhost:8000`.

Comando para rodar a aplicação diretamente (sem Docker), com virtualenv/`pip install`/`python main.py`: **A confirmar** (não há script nem instrução no repositório para esse caminho).

## Como rodar os testes e popular o banco com dados de exemplo

**Testes**

Configuração de testes em [pytest.ini](pytest.ini) (`pythonpath = .`) e suíte em [src/tests/services/test_event_service.py](src/tests/services/test_event_service.py), cobrindo `event_service` (criação, listagem, busca por token, atualização). Comando exato de execução (ex.: `pytest` a partir de qual diretório, com quais variáveis de ambiente): **A confirmar**.

**Popular dados de exemplo**

Script [scripts/seed.py](scripts/seed.py): cria eventos de exemplo chamando a API HTTP (`POST /api/events/`), evitando duplicar títulos já existentes (consulta `GET /api/events/` antes de criar).

```
python scripts/seed.py --base-url http://localhost:8000
```

- `--base-url` é opcional, default `http://localhost:8000` ([scripts/seed.py:96-100](scripts/seed.py#L96-L100))
- Requer a aplicação já em execução e acessível na URL informada

## Como provisionar a infraestrutura com Terraform

Os arquivos em [terraform/](terraform/) provisionam um cluster EKS na AWS:

- [terraform/main.tf](terraform/main.tf) define três módulos:
  - `vpc` (`terraform-aws-modules/vpc/aws ~> 5.8`): cria a VPC, subnets públicas e privadas, NAT gateway
  - `eks` (`terraform-aws-modules/eks/aws ~> 20.24`): cria o cluster EKS, node group gerenciado, e o addon `aws-ebs-csi-driver`
  - `ebs_csi_irsa_role` (`terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks ~> 5.39`): cria a role IAM (IRSA) usada pelo EBS CSI driver
- Variáveis (com defaults) em [terraform/variables.tf](terraform/variables.tf): região `us-east-1`, nome do projeto/cluster `encontros-tech`, CIDR da VPC `10.0.0.0/16`, AZs `us-east-1a`/`us-east-1b`, versão do Kubernetes `1.30`, tipo de instância dos nós `t3.medium`, tamanho do node group entre 1 e 3 (desejado 2)
- Saídas em [terraform/outputs.tf](terraform/outputs.tf): `cluster_name`, `cluster_endpoint`, `cluster_certificate_authority_data` (sensível) e `configure_kubectl` (comando pronto para configurar o `kubectl`)

Comandos:

```
cd terraform
terraform init
terraform plan
terraform apply
```

Após o `apply`, configure o `kubectl` com o comando exibido na saída `configure_kubectl`:

```
aws eks update-kubeconfig --region <region> --name <cluster_name>
```

Backend remoto de state (S3/DynamoDB): não configurado em [terraform/providers.tf](terraform/providers.tf) — o state atual é local (`terraform/terraform.tfstate`). **A confirmar** se há um backend remoto pretendido para uso em equipe.

## Como fazer o deploy no cluster Kubernetes

Todos os recursos estão em um único arquivo, [k8s/encontros-tech.yaml](k8s/encontros-tech.yaml), como múltiplos documentos YAML na seguinte ordem:

1. `Namespace encontros-tech`
2. `Secret encontros-tech-secret` (credenciais do Postgres e `DATABASE_URL`)
3. `ConfigMap encontros-tech-config` (demais variáveis de ambiente da aplicação)
4. `PersistentVolumeClaim postgres-data` (1Gi, `storageClassName: gp2`)
5. `Deployment postgres` (imagem `postgres:16-alpine`, 1 réplica, probes via `pg_isready`)
6. `Service postgres` (porta 5432, ClusterIP padrão)
7. `Deployment encontros-tech` (imagem `teclinux/encontros-tech`, 2 réplicas, `initContainer` que aguarda `postgres:5432` responder antes de subir o container principal, probes de readiness em `/ready` e liveness em `/health`)
8. `Service encontros-tech` (tipo `LoadBalancer`, porta 80 → 8000 no container)

Aplicar tudo de uma vez (o próprio arquivo já respeita a ordem de dependência entre os recursos):

```
kubectl apply -f k8s/encontros-tech.yaml
```

A imagem `teclinux/encontros-tech` referenciada no Deployment precisa existir em um registry acessível pelo cluster; o comando de build/push dessa imagem não está definido em nenhum arquivo do repositório (**A confirmar**).

Como obter a URL/IP externo do serviço após o deploy: **A confirmar** (o Service é do tipo `LoadBalancer`, mas não há documentação de como recuperar o endpoint no repositório).

## Endpoints de saúde

- **`GET /health`** (liveness): sempre retorna `{"status": "ok"}` com HTTP 200, sem checar dependências externas ([src/routers/health_router.py:7-9](src/routers/health_router.py#L7-L9), [src/services/health_service.py:7-8](src/services/health_service.py#L7-L8)). Usado como `livenessProbe` no Deployment `encontros-tech` do Kubernetes.
- **`GET /ready`** (readiness): executa `SELECT 1` no banco de dados; se a query for bem-sucedida retorna `{"status": "ready"}` com HTTP 200; se falhar, retorna `{"status": "not ready", "reason": <mensagem do erro>}` com HTTP 503 ([src/routers/health_router.py:11-18](src/routers/health_router.py#L11-L18), [src/services/health_service.py:10-16](src/services/health_service.py#L10-L16)). Usado como `readinessProbe` no Deployment `encontros-tech` do Kubernetes.

## Variáveis de ambiente

Lidas pela aplicação em [src/core/settings.py](src/core/settings.py), com descrições em [.env.exemple](.env.exemple) / [src/.env.example](src/.env.example):

| Variável | Descrição | Default |
|---|---|---|
| `DATABASE_URL` | URL completa de conexão com o PostgreSQL (`postgresql://usuario:senha@host:porta/nome_banco`) | `postgresql://encontros_tech:encontros_tech@localhost:5432/encontros_tech` |
| `APP_TITLE` | Título da aplicação | `Encontros Tech` |
| `DEBUG` | Ativa modo debug do Flask | `false` |
| `HOST` | Host onde a aplicação escuta | `0.0.0.0` |
| `PORT` | Porta onde a aplicação escuta | `8000` |
| `LOG_LEVEL` | Nível de log (`DEBUG` se `DEBUG=true`, senão `INFO`) | `INFO` |
| `LOG_FORMAT` | Formato do log (`colored` ou `simple`) | `colored` |
| `SERVICE_NAME` | Nome do serviço, usado em telemetria/logs | `encontros-tech` |
| `SERVICE_VERSION` | Versão do serviço, exposta na métrica `app_info` | `1.0.0` |
| `PROMETHEUS_MULTIPROC_DIR` | Diretório para métricas Prometheus em ambiente multiprocess (Gunicorn) | `/tmp/prometheus_multiproc` |

Variáveis usadas apenas pelo `docker-compose.yml` para configurar o container do Postgres (não lidas diretamente pelo código Python da aplicação):

| Variável | Descrição | Default |
|---|---|---|
| `POSTGRES_USER` | Usuário do PostgreSQL | `encontros_tech` |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL | `encontros_tech` |
| `POSTGRES_DB` | Nome do banco de dados | `encontros_tech` |

`PROMETHEUS_PORT` aparece documentada em [.env.exemple](.env.exemple) e [src/.env.example](src/.env.example) (default `9090`), mas não é lida em nenhum arquivo Python encontrado no repositório — **A confirmar** se está efetivamente em uso.
