# Kubernetes deployment

Минимальные манифесты для локального Kubernetes-кластера.

Состав:

- `namespace.yaml` — namespace `fastapi-auth`;
- `configmap.yaml` — env-настройки приложения для запуска в Kubernetes;
- `secret.yaml` — секрет подписи mock access token;
- `deployment.yaml` — FastAPI pod с readiness/liveness probes;
- `service.yaml` — ClusterIP service для доступа внутри кластера.
- `ingress.yaml` — внешний доступ к сервису через `http://hello.local`.

В Kubernetes-демо Consul, Vault и Kafka отключены через env, чтобы pod стабильно запускался без внешних сервисов.
Секрет токена передаётся через Kubernetes Secret.

## Что проверяется

- `APP_ENV=production` приходит из ConfigMap `fastapi-auth-config`;
- `APP_TOKEN_SECRET` приходит из Secret `fastapi-auth-secret`;
- readinessProbe и livenessProbe ходят на `/health`;
- Ingress маршрутизирует `http://hello.local` в `fastapi-auth-service`.

## Минимальная проверка

```bash
kubectl apply -f k8s/
kubectl get pods -n fastapi-auth
kubectl describe pod -n fastapi-auth -l app=fastapi-auth
kubectl get ingress -n fastapi-auth
```

Проверить env из ConfigMap и Secret:

```bash
kubectl exec -n fastapi-auth deploy/fastapi-auth -- printenv APP_ENV
kubectl exec -n fastapi-auth deploy/fastapi-auth -- printenv APP_TOKEN_SECRET
```

Для Ingress нужен ingress controller. В minikube его можно включить так:

```bash
minikube addons enable ingress
```

Добавить в `/etc/hosts`:

```text
127.0.0.1 hello.local
```

Проверить внешний доступ:

```bash
curl http://hello.local/health
```
