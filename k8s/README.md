# Kubernetes deployment

Минимальные манифесты для локального Kubernetes-кластера.

Состав:

- `namespace.yaml` — namespace `fastapi-auth`;
- `configmap.yaml` — env-настройки приложения для запуска в Kubernetes;
- `secret.yaml` — секрет подписи mock access token;
- `deployment.yaml` — FastAPI pod с readiness/liveness probes;
- `service.yaml` — ClusterIP service для доступа внутри кластера.

В Kubernetes-демо Consul, Vault и Kafka отключены через env, чтобы pod стабильно запускался без внешних сервисов.
Секрет токена передаётся через Kubernetes Secret.
