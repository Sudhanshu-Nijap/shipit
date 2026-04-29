def generate_k8_yaml(name, image, domain):
    return f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: app
        image: {image}
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "500m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: {name}-service
spec:
  selector:
    app: {name}
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls.certresolver: le
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - {name}.{domain}
  rules:
  - host: {name}.{domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {name}-service
            port:
              number: 80
"""