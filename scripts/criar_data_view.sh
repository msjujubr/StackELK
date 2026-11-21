#!/usr/bin/env bash
set -euo pipefail

KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
DATA_VIEW_TITLE="filebeat-*"

printf 'Aguardando o Kibana em %s' "$KIBANA_URL"
for attempt in $(seq 1 60); do
  if curl -fsS "$KIBANA_URL/api/status" >/dev/null 2>&1; then
    printf '\nKibana disponível.\n'
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    printf '\nKibana não ficou disponível dentro do tempo esperado.\n' >&2
    exit 1
  fi
  printf '.'
  sleep 5
done

EXISTING=$(curl -fsS -H 'kbn-xsrf: true' "$KIBANA_URL/api/data_views" || true)
if printf '%s' "$EXISTING" | grep -Fq 'filebeat-*'; then
  echo 'A Data View filebeat-* já existe; nenhuma alteração foi necessária.'
  exit 0
fi

curl --fail-with-body -sS \
  -X POST "$KIBANA_URL/api/data_views/data_view" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  -d '{"data_view":{"title":"filebeat-*","name":"Prática 03 - Logs Nginx","timeFieldName":"@timestamp"}}'
printf '\nData View criada. Abra o Kibana > Discover e selecione filebeat-*.\n'
