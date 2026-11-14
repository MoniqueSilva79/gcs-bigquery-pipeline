# 📦➡️📊 Pipeline Orientado a Eventos: Cloud Storage → BigQuery → Looker Studio

Pipeline de dados **serverless** no Google Cloud: quando um arquivo CSV chega ao bucket, uma **Cloud Function** valida e carrega os dados no **BigQuery** automaticamente. No fim, um dashboard no **Looker Studio** mostra os resultados.

## 🏗️ Arquitetura
```
CSV de vendas ──upload──► Cloud Storage (bucket "landing")
                                │  evento: object finalized (Eventarc)
                                ▼
                      Cloud Function (Python)
                       • valida nome/extensão
                       • load job no BigQuery (append)
                                ▼
                      BigQuery: dataset vendas.pedidos
                                ▼
                      Looker Studio (dashboard)
```

## 🧰 Tecnologias
Cloud Storage · Cloud Functions (2ª geração) · Eventarc · BigQuery · Looker Studio · Python

## 🚀 Passo a passo
```bash
export PROJECT_ID=seu-projeto
export REGION=southamerica-east1
export BUCKET=${PROJECT_ID}-landing

gcloud config set project $PROJECT_ID
gcloud services enable cloudfunctions.googleapis.com run.googleapis.com eventarc.googleapis.com \
  bigquery.googleapis.com storage.googleapis.com cloudbuild.googleapis.com

# 1. Bucket de entrada
gcloud storage buckets create gs://$BUCKET --location=$REGION

# 2. Dataset e tabela no BigQuery
bq --location=$REGION mk -d vendas
bq mk --table vendas.pedidos schema.json

# 3. Permissão para o Cloud Storage publicar eventos (necessária no gen2)
SA=$(gcloud storage service-agent --project=$PROJECT_ID)
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA" --role=roles/pubsub.publisher

# 4. Deploy da função disparada pelo upload
gcloud functions deploy load-to-bq \
  --gen2 --runtime=python312 --region=$REGION \
  --source=. --entry-point=gcs_to_bigquery \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=$BUCKET" \
  --set-env-vars=BQ_TABLE=$PROJECT_ID.vendas.pedidos

# 5. Teste: envie o CSV de exemplo
gcloud storage cp sample_data/pedidos_2026_01.csv gs://$BUCKET/

# 6. Confira no BigQuery
bq query --use_legacy_sql=false 'SELECT estado, SUM(valor) total FROM vendas.pedidos GROUP BY estado ORDER BY total DESC'
```

## 📊 Dashboard
No [Looker Studio](https://lookerstudio.google.com), crie uma fonte de dados BigQuery apontando para `vendas.pedidos` e monte gráficos de receita por dia, estado e categoria.

## 🔒 Boas práticas
- A função usa a conta de serviço com papéis mínimos (`BigQuery Data Editor`, `BigQuery Job User`, `Storage Object Viewer`)
- Arquivos que não são `.csv` são ignorados
- Tabela particionada por data reduz custo de consulta (veja *Próximos passos*)

## 🗺️ Próximos passos
- [ ] Particionar a tabela por `data_pedido`
- [ ] Mover arquivos processados para um bucket `processed/`
- [ ] Alertas no Cloud Monitoring em caso de erro
- [ ] Infraestrutura como código com Terraform
