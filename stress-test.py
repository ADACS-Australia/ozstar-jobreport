import subprocess
import time
import random
import argparse
from concurrent.futures import ThreadPoolExecutor

def get_jobs():
  """Get job IDs in the R (running) state using squeue."""
  try:
    result = subprocess.run(['squeue', '--state=R', '--format=%i'], capture_output=True, text=True, check=True)
    job_ids = result.stdout.strip().split('\n')[1:]  # Skip the header
    return job_ids
  except subprocess.CalledProcessError as e:
    print(f"Error querying squeue: {e}")
    return []

def call_jobsummary(job_id):
  """Call the jobsummary script for a given job ID."""
  try:
    start_time = time.time()
    result = subprocess.run(['jobsummary', job_id], capture_output=True, text=True, check=True, timeout=90)
    end_time = time.time()

    # Check that the stdout contains "Elapsed", meaning it printed all the way to the end
    if "Elapsed" in result.stdout:
      return end_time - start_time

  except subprocess.TimeoutExpired:
    return f"Timeout calling jobsummary for job {job_id}"

  except subprocess.CalledProcessError as e:
    return f"Error calling jobsummary for job {job_id}: {e}"

def main():
  parser = argparse.ArgumentParser(description='Stress test jobsummary script')
  parser.add_argument('num_jobs', type=int, help='Number of jobs to test')
  parser.add_argument('sleep_time', type=int, help='Sleep time between tests')
  parser.add_argument('num_tests', type=int, help='Number of times to test')
  args = parser.parse_args()

  print(f"Stress testing jobsummary script: querying {args.num_jobs} random jobs every {args.sleep_time} seconds for {args.num_tests} tests")

  for _ in range(args.num_tests):
    job_ids = get_jobs()

    # Randomly select n jobs to test
    n = args.num_jobs
    job_ids = random.sample(job_ids, k=n)


    with ThreadPoolExecutor(max_workers=n) as executor:
      futures = [executor.submit(call_jobsummary, job_id) for job_id in job_ids]
      for future in futures:
        future.result()  # Wait for all futures to complete

    # Count the number of successes (the number of times returned)
    times = [future.result() for future in futures if isinstance(future.result(), float)]
    success_count = len(times)

    # Get the minimum, maximum, and average time
    min_time = min(times) if times else 0
    max_time = max(times) if times else 0
    avg_time = sum(times) / len(times) if times else 0

    print(f"{success_count}/{n} jobs succeeded in min/ave/max time: {min_time:.2f}/{avg_time:.2f}/{max_time:.2f} seconds")

    time.sleep(args.sleep_time)

if __name__ == "__main__":
  main()
