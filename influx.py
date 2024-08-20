from influxdb_client import InfluxDBClient


class InfluxQuery:
    # # InfluxDB connection
    # URL = "http://influxdb:8086"
    # ORG = "swinburne"
    # TOKEN = "<read only token>"

    def __init__(self, config_file, retries=3, search_window="7d", bucket="jobmon-stats", lustre_bucket="lustre-jobstats"):
        self.search_window = search_window
        self.bucket = bucket
        self.lustre_bucket = lustre_bucket
        self.influx_client = InfluxDBClient.from_config_file(
            config_file, retries=retries
        )
        self.health_check()
        self.influx_query_api = self.influx_client.query_api()
        self.query_check()

    def health_check(self):
        health = self.influx_client.health()
        if health.status != "pass":
            raise Exception("Warning: could not connect to InfluxDB server")

    def query_check(self):
        # Perform a simple query to validate the organization
        query = f'from(bucket: "{self.bucket}") |> range(start: -1m) |> limit(n:1)'
        self.influx_query_api.query(query)

    def query(self, job_query):
        return self.influx_query_api.query(job_query)

    def get_max_mem(self, job_id):
        """
        Query Influx for slurm memory stats
        """

        # Query for the max memory usage of any node in the job
        job_query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: -{self.search_window})
        |> filter(fn: (r) => r["_measurement"] == "job_max_memory")
        |> filter(fn: (r) => r["job_id"] == "{job_id}")
        |> last()
        """

        job_results = self.query(job_query)

        if len(job_results) > 0:
            # Get the max value and convert MB to B
            return job_results[0].records[0].get_value() * 1024**2
        else:
            return None

    def get_lustre_jobstats(self, job_id):
        """
        Query Influx for the Lustre jobstats
        """

        job_query = f"""
        from(bucket: "{self.lustre_bucket}")
        |> range(start: -{self.search_window})
        |> filter(fn: (r) => r["_measurement"] == "lustre")
        |> filter(fn: (r) => r["job"] == "{job_id}")
        |> last()
        """

        job_results = self.query(job_query)

        data = {}

        for table in job_results:
            fs = table.records[0]["fs"]
            server = table.records[0]["server"]
            field = table.records[0].get_field()

            if fs not in data:
                data[fs] = {}
            if server not in data[fs]:
                data[fs][server] = {}
            if field not in data[fs][server]:
                data[fs][server][field] = {"ts": [], "value": []}

            for record in table:
                ts = int(record.get_time().timestamp())
                data[fs][server][field]["ts"] += [ts]
                data[fs][server][field]["value"] += [record.get_value()]

        return data

    def get_avg_cpu(self, job_id):
        """
        Query Influx for CPU usage and calculate the average
        """

        job_query = f"""
        from(bucket: "{self.bucket}")
        |> range(start: -{self.search_window})
        |> filter(fn: (r) => r["_measurement"] == "average_cpu_usage")
        |> filter(fn: (r) => r["job_id"] == "{job_id}")
        |> mean()
        """

        job_results = self.query(job_query)

        if len(job_results) > 0:
            return job_results[0].records[0].get_value()
        else:
            return None
