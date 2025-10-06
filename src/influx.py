import time
import warnings
import numpy as np
from datetime import datetime
from influxdb_client import InfluxDBClient
from influxdb_client.client.warnings import MissingPivotFunction

warnings.simplefilter("ignore", MissingPivotFunction)

class InfluxQuery:
    # # InfluxDB connection
    # URL = "http://influxdb:8086"
    # ORG = "swinburne"
    # TOKEN = "<read only token>"

    DEFAULT_SEARCH_WINDOW = 604800      # seconds (7 days)

    def __init__(
        self,
        config_file,
        retries=3,
        bucket="jobmon-stats",
        lustre_bucket="lustre-jobstats",
        downsampled_bucket="jobmon-stats-downsampled",
        downsampled_lustre_bucket="lustre-jobstats-downsampled",
        verbose=False,
    ):
        """
        Initialize InfluxDB client and set up connection parameters.

        Args:
            config_file: Path to InfluxDB configuration file
            retries: Number of connection retries (default: 3)
            bucket: Main bucket name for job statistics
            lustre_bucket: Bucket name for Lustre filesystem statistics
            downsampled_bucket: Downsampled version of main bucket
            downsampled_lustre_bucket: Downsampled version of Lustre bucket
            verbose: Enable verbose logging output
        """
        self.verbose = verbose
        # Set the default search window (can be changed later).
        self.set_search_window(int(time.time()) - self.DEFAULT_SEARCH_WINDOW)
        self.bucket = bucket
        self.lustre_bucket = lustre_bucket
        self.downsampled_bucket = downsampled_bucket
        self.downsampled_lustre_bucket = downsampled_lustre_bucket
        self.use_downsampled = False
        self.influx_client = InfluxDBClient.from_config_file(
            config_file, retries=retries
        )
        self.health_check()
        self.influx_query_api = self.influx_client.query_api()
        self.check_buckets()
        self._get_bucket_retention()

    def check_buckets(self):
        """
        Verify that all required InfluxDB buckets are accessible.

        Raises:
            Exception: If any bucket is not accessible
        """
        if self.verbose: print("Checking InfluxDB buckets...")
        buckets = [
            self.bucket,
            self.lustre_bucket,
            self.downsampled_bucket,
            self.downsampled_lustre_bucket
        ]
        for bucket in buckets:
            if self.influx_client.buckets_api().find_bucket_by_name(bucket) is None:
                raise Exception(f"Bucket '{bucket}' is not accessible")
            elif self.verbose:
                print(f"Bucket {bucket} is OK")

    def _get_bucket_retention(self):
        """
        Retrieve retention periods for main and Lustre buckets from InfluxDB.

        Sets instance variables for main_bucket_retention and lustre_bucket_retention
        in seconds.
        """
        self.main_bucket_retention = self.influx_client.buckets_api().find_bucket_by_name(self.bucket).retention_rules[0].every_seconds
        self.lustre_bucket_retention = self.influx_client.buckets_api().find_bucket_by_name(self.lustre_bucket).retention_rules[0].every_seconds

        if self.verbose:
            print("Main bucket retention period (s)  : ", self.main_bucket_retention)
            print("Lustre bucket retention period (s): ", self.lustre_bucket_retention)

    def set_search_window(self, start, stop=None):
        """
        Set the time window for InfluxDB queries.

        Args:
            start: Unix timestamp for the start of the search window
            stop: Unix timestamp for the end of the search window (optional)
        """
        self.search_window_start = start
        self.search_window_stop = stop
        if stop:
            self.search_window_str = f"start: {start}, stop: {stop}"
        else:
            self.search_window_str = f"start: {start}"

        if self.verbose:
            print("Search window set to: ", f'"{self.search_window_str}"')
            start_h = datetime.fromtimestamp(start).strftime("%Y-%m-%d %H:%M:%S")
            stop_h = datetime.fromtimestamp(stop) if stop else datetime.now()
            stop_h = stop_h.strftime("%Y-%m-%d %H:%M:%S")
            print(f" start: {start_h}")
            print(f"  stop: {stop_h}")

    def health_check(self):
        """
        Check the health status of the InfluxDB server.

        Raises:
            Exception: If InfluxDB server is not reachable or unhealthy
        """
        if self.verbose: print("Checking InfluxDB health...")
        health = self.influx_client.health()
        if health.status != "pass":
            raise Exception("Warning: could not connect to InfluxDB server")
        elif self.verbose:
            print("InfluxDB health is OK")

    def get_bucket(self, bucket_type="main"):
        """
        Get the appropriate bucket to use based on the search window and bucket type.

        Args:
            bucket_type (str): Type of bucket to get ("main" or "lustre")

        Returns:
            str: Bucket name to use (either main bucket or downsampled bucket)

        Raises:
            ValueError: If bucket_type is not "main" or "lustre"
        """
        if bucket_type == "main":
            retention_period = self.main_bucket_retention
            regular_bucket = self.bucket
            downsampled_bucket = self.downsampled_bucket
        elif bucket_type == "lustre":
            retention_period = self.lustre_bucket_retention
            regular_bucket = self.lustre_bucket
            downsampled_bucket = self.downsampled_lustre_bucket
        else:
            raise ValueError(f"bucket_type must be 'main' or 'lustre', got '{bucket_type}'")

        # If outside bucket retention period, use downsampled bucket
        use_downsampled = self.search_window_start < (int(time.time()) - retention_period)

        if self.verbose:
            print(f"Using downsampled {bucket_type} bucket: ", use_downsampled)

        if use_downsampled:
            return downsampled_bucket
        else:
            return regular_bucket

    def get_lustre_bucket(self):
        """
        Get the appropriate Lustre bucket to use based on the search window.

        Returns:
            str: Lustre bucket name to use (either main or downsampled bucket)
        """
        return self.get_bucket("lustre")

    def query(self, job_query, data_frame=False):
        """
        Execute a query against the InfluxDB database.

        Args:
            job_query: The InfluxDB query string to execute

        Returns:
            Query result from InfluxDB
        """
        if self.verbose:
            print("Executing query:")
            print(job_query)

        if data_frame:
            df = self.influx_query_api.query_data_frame(job_query)

            # Return None if no data
            if df is None or len(df) == 0:
                return None

            df = df.drop(columns=['result', 'table'], errors='ignore')

            # Convert timestamp to Unix seconds and set as index
            df.index = df['_time'].astype(np.int64) // 10**9
            df.index = df.index - df.index[0]  # Set time=0 to start of job
            df.index.name = 'time'
            df = df.drop(columns=['_time'])

            # sort by index (time)
            df.sort_index(inplace=True)
            return df

        else:
            return self.influx_query_api.query(job_query)

    def get_max_mem(self, job_id):
        """
        Query InfluxDB for maximum memory usage of a job.

        Args:
            job_id: The job ID to query for

        Returns:
            int: Maximum memory usage in bytes, or None if no data found
        """

        # Query for the max memory usage of any node in the job
        job_query = f"""
        from(bucket: "{self.get_bucket()}")
        |> range({self.search_window_str})
        |> filter(fn: (r) => r["_measurement"] == "job_max_memory")
        |> filter(fn: (r) => r["job_id"] == "{job_id}")
        |> last()
        """

        job_results = self.query(job_query)

        if len(job_results) > 0:
            # Get the max value and convert MB to B
            result = job_results[0].records[0].get_value() * 1024**2
            if self.verbose:
                print("(get_max_mem) result: ", result)
            return result
        else:
            return None

    def get_lustre_jobstats(self, job_id):
        """
        Query InfluxDB for Lustre filesystem statistics for a specific job.

        Args:
            job_id: The job ID to query for

        Returns:
            dict: Nested dictionary containing Lustre statistics organized by filesystem,
                  server type, and field with timestamp and value arrays
        """

        job_query = f"""
        from(bucket: "{self.get_lustre_bucket()}")
        |> range({self.search_window_str})
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

        if self.verbose:
            print("(get_lustre_jobstats) result:")
            print(data)

        return data

    def get_avg_usage(self, job_id, measurement_type="cpu"):
        """
        Query InfluxDB for CPU or GPU usage statistics and calculate the average.

        Args:
            job_id: The job ID to query for
            measurement_type (str): Type of measurement to get ("cpu" or "gpu")

        Returns:
            float: Average usage percentage, or None if no data found

        Raises:
            ValueError: If measurement_type is not "cpu" or "gpu"
        """
        if measurement_type == "cpu":
            measurement = "average_cpu_usage"
        elif measurement_type == "gpu":
            measurement = "average_gpu_usage"
        else:
            raise ValueError(f"measurement_type must be 'cpu' or 'gpu', got '{measurement_type}'")

        job_query = f"""
        from(bucket: "{self.get_bucket()}")
        |> range({self.search_window_str})
        |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        |> filter(fn: (r) => r["job_id"] == "{job_id}")
        |> mean()
        """

        job_results = self.query(job_query)

        if len(job_results) > 0:
            result = job_results[0].records[0].get_value()
            if self.verbose:
                print(f"(get_avg_usage) {measurement_type} result: ", result)
            return result
        else:
            return None

    def get_avg_cpu(self, job_id):
        """
        Query InfluxDB for CPU usage statistics and calculate the average.

        Args:
            job_id: The job ID to query for

        Returns:
            float: Average CPU usage percentage, or None if no data found
        """
        return self.get_avg_usage(job_id, "cpu")

    def get_avg_gpu(self, job_id):
        """
        Query InfluxDB for GPU usage statistics and calculate the average.

        Args:
            job_id: The job ID to query for

        Returns:
            float: Average GPU usage percentage, or None if no data found
        """
        return self.get_avg_usage(job_id, "gpu")

    def get_usage_series(self, job_id, measurement_type="cpu"):
        """
        Query InfluxDB for CPU or GPU usage time series data.

        Args:
            job_id: The job ID to query for
            measurement_type (str): Type of measurement to get ("cpu" or "gpu")

        Returns:
            pandas.DataFrame: DataFrame indexed by Unix timestamp (seconds), with a column for usage values,
                              or None if no data found

        Raises:
            ValueError: If measurement_type is not "cpu" or "gpu"
        """
        if measurement_type == "cpu":
            measurement = "average_cpu_usage"
        elif measurement_type == "gpu":
            measurement = "average_gpu_usage"
        else:
            raise ValueError(f"measurement_type must be 'cpu' or 'gpu', got '{measurement_type}'")

        job_query = f"""
        from(bucket: "{self.get_bucket()}")
        |> range({self.search_window_str})
        |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        |> filter(fn: (r) => r["job_id"] == "{job_id}")
        |> filter(fn: (r) => r["_field"] == "value")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> rename(columns: {{value: "{measurement_type}"}})
        |> keep(columns: ["_time", "{measurement_type}"])
        """

        df = self.query(job_query, data_frame=True)

        # Return None if no data
        if df is None or len(df) == 0:
            return None

        if self.verbose:
            print("(get_usage_series)")
            print("Result:")
            print(df)
        return df

    def get_cpu_series(self, job_id):
        """
        Query InfluxDB for CPU usage time series data.

        Args:
            job_id: The job ID to query for

        Returns:
            dict: Dictionary containing 'time' (timestamps as int64) and 'value' (CPU usage as float64) numpy arrays,
                  or None if no data found
        """
        return self.get_usage_series(job_id, "cpu")

    def get_gpu_series(self, job_id):
        """
        Query InfluxDB for GPU usage time series data.

        Args:
            job_id: The job ID to query for

        Returns:
            dict: Dictionary containing 'time' (timestamps as int64) and 'value' (GPU usage as float64) numpy arrays,
                  or None if no data found
        """
        return self.get_usage_series(job_id, "gpu")

    def get_lustre_rates(self, job_id, field='read_bytes', server="oss"):
        """Get Lustre filesystem I/O rates for a specific field + server combination."""

        query = f"""
        from(bucket: "{self.get_lustre_bucket()}")
        |> range({self.search_window_str})
        |> filter(fn: (r) => r["_measurement"] == "lustre")
        |> filter(fn: (r) => r["job"] == "{job_id}")
        |> filter(fn: (r) => r["_field"] == "{field}")
        |> filter(fn: (r) => r["server"] == "{server}")
        |> derivative(unit: 1s, nonNegative: false)
        |> pivot(rowKey:["_time"], columnKey: ["fs"], valueColumn: "_value")
        |> drop(columns: ["_start", "_stop", "_measurement", "job", "server", "_field"])
        """

        df = self.query(query, data_frame=True)

        # Return None if no data
        if df is None or len(df) == 0:
            return None

        if self.verbose:
            print(f"(get_lustre_rates) {field} result:")
            print(df)

        return df
