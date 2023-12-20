import sys
import requests
import time
import yaml


class EndpointMonitor:
    def __init__(self, endpoints, interval):
        self.endpoints = endpoints
        self.results = {endpoint["url"]: {"total_checks": 0, "successful_checks": 0} for endpoint in endpoints}
        self.interval_seconds = interval

    def check_health(self, endpoint):
        try:
            start_time = time.time()
            headers = endpoint.get("headers", {})
            method = endpoint.get("method", "GET")

            # Determine the response based on the method
            if method == "GET":
                response = requests.get(endpoint["url"], headers=headers)
            elif method == "POST":
                body = endpoint.get("body", None)
                response = requests.post(endpoint["url"], headers=headers, json=body)
            else:
                print(f"Unsupported HTTP method for {endpoint['name']} ({endpoint['url']}): {method}")
                return

            # Calculate the response time
            response_time = (time.time() - start_time) * 1000

            # Check whether endpoint is 'UP' or 'DOWN' based on response status code and response time
            if response.ok and 200 <= response.status_code < 300 and response_time < 500:
                self.results[endpoint["url"]]["successful_checks"] += 1
                print(f"Endpoint {endpoint['name']} ({endpoint['url']}) is UP. Response time: {response_time:.2f} ms")
            else:
                print(f"Endpoint {endpoint['name']} ({endpoint['url']}) is DOWN. Response time: {response_time:.2f} ms")

        except requests.exceptions.RequestException as e:
            print(f"Error checking health for {endpoint['name']} ({endpoint['url']}): {e}")

        self.results[endpoint["url"]]["total_checks"] += 1

    def log_domain_availability(self):
        domain_results = {}
        for endpoint_url, result in self.results.items():
            # Get the domain name
            domain = requests.compat.urlparse(endpoint_url).netloc
            if domain not in domain_results:
                domain_results[domain] = {"total_checks": 0, "successful_checks": 0}
            domain_results[domain]["total_checks"] += result["total_checks"]
            domain_results[domain]["successful_checks"] += result["successful_checks"]

        for domain, result in domain_results.items():
            # Calculate the availability percentage
            availability_percentage = (result["successful_checks"] / result["total_checks"]) * 100 if result["total_checks"] > 0 else 0
            print(f"Overall Availability Percentage for {domain}: {availability_percentage:.2f}%")

    def monitor(self):
        try:
            while True:
                for endpoint in self.endpoints:
                    self.check_health(endpoint)

                self.log_domain_availability()
                # Wait for the interval seconds
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")


def load_endpoints_from_yaml(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        return data if isinstance(data, list) else []


if __name__ == "__main__":
    # Retrieve YAML file path from arguments
    yaml_file_path = sys.argv[1]

    # Retrieve interval for healthcheck from arguments
    interval = int(sys.argv[2])

    # Load endpoints from YAML file
    endpoints = load_endpoints_from_yaml(yaml_file_path)

    monitor = EndpointMonitor(endpoints, interval)
    monitor.monitor()
