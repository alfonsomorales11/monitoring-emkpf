## 1 - Deploy kibana and elasticsearch cluster

```
docker compose -f ./elastic/kibanadocker/docker-compose.yml up -d
```

## 2 - Create index mapping for fluentd in elasticsearch
```
PUT _template/logstash
{
  "index_patterns": [
    "logstash-*"
  ],
  "mappings": {
    "dynamic_templates": [
      {
        "message_field": {
          "path_match": "message",
          "mapping": {
            "norms": false,
            "type": "text"
          },
          "match_mapping_type": "string"
        }
      },
      {
        "another_message_field": {
          "path_match": "MESSAGE",
          "mapping": {
            "norms": false,
            "type": "text"
          },
          "match_mapping_type": "string"
        }
      },
      {
        "strings_as_keyword": {
          "mapping": {
            "ignore_above": 1024,
            "type": "keyword"
          },
          "match_mapping_type": "string"
        }
      }
    ],
    "properties": {
      "@timestamp": {
        "type": "date"
      }
    }
  }
}
```

## 3 - Create fluentd configmap
```
kubectl create configmap fluentd-conf --from-file=./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/kubernetes.conf --namespace=kube-system

kubectl apply -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/configMap.yaml
```

## 4 - Deploy fluentd daemonset
```
kubectl create -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/fluentd-daemonset-elasticsearch-rbac.yaml
```

## 5 - Deploy metricbeat
```
helm install metricbeat ./metricbeat/Monitoring/Charts/metricbeat
```

## 6 - Deploy prometheus
```
helm install prometheus -n kube-system prometheus-community/prometheus -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/prometheus_custom.yaml
```

## 7 - Deploy Python app
```
kubectl create -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/cloud-vote-all-in-one-redis-aks-prometheus.yaml
```

## 8 - Delete all
```
kubectl delete configmap fluentd-conf -n kube-system
kubectl delete -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/configMap.yaml
kubectl delete -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/fluentd-daemonset-elasticsearch-rbac.yaml
helm delete metricbeat
helm delete prometheus -n kube-system
kubectl delete -f ./prometheus-fluentd/cloud-voting-app-redis/cncf-projects/cloud-vote-all-in-one-redis-aks-prometheus.yaml
```