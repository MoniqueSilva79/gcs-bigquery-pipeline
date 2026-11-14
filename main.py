"""Cloud Function (2ª geração): carrega CSVs do Cloud Storage no BigQuery."""
import os

import functions_framework
from google.cloud import bigquery

BQ_TABLE = os.environ["BQ_TABLE"]  # ex.: projeto.vendas.pedidos
client = bigquery.Client()


@functions_framework.cloud_event
def gcs_to_bigquery(cloud_event):
    data = cloud_event.data
    bucket, name = data["bucket"], data["name"]

    if not name.lower().endswith(".csv"):
        print(f"Ignorado (não é CSV): {name}")
        return

    uri = f"gs://{bucket}/{name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        max_bad_records=10,
    )

    job = client.load_table_from_uri(uri, BQ_TABLE, job_config=job_config)
    job.result()  # espera terminar e lança erro se falhar

    print(f"OK: {job.output_rows} linhas de {uri} carregadas em {BQ_TABLE}")
