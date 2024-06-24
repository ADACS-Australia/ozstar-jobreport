import influx_config
from influxdb_client import InfluxDBClient

influx_client = InfluxDBClient(
    url=influx_config.URL,
    org=influx_config.ORG,
    token=influx_config.TOKEN,
    timeout="10s",
    retries=3,
)

influx_query_api = influx_client.query_api()


def query(query):
    return influx_query_api.query(query, org=influx_config.ORG)
