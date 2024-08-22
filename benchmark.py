import subprocess
import json
import os
import re

def run_wrk(url, duration='30s', threads=2, connections=10):
    """
    Run wrk with the specified URL and parameters.

    Args:
        url (str): The URL to benchmark.
        duration (str): Duration of the test (e.g., '30s').
        threads (int): Number of threads to use.
        connections (int): Number of connections to use.

    Returns:
        dict: Parsed results from wrk.
    """
    command = [
        'wrk', 
        '-t', str(threads), 
        '-c', str(connections), 
        '-d', duration, 
        '--latency', 
        url
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout
    
    # Parsing the wrk output
    parsed_data = parse_wrk_output(output)
    
    return parsed_data

def parse_wrk_output(text):
    
    result = {}

    # Extracting the URL and test duration
    url_match = re.search(r'@ (http[^\s]+)', text)
    duration_match = re.search(r'Running (\d+)s test', text)
    
    if url_match and duration_match:
        result['url'] = url_match.group(1)
        result['duration'] = int(duration_match.group(1))

    # Extracting thread and connection details
    threads_connections_match = re.search(r'(\d+) threads and (\d+) connections', text)
    if threads_connections_match:
        result['threads'] = int(threads_connections_match.group(1))
        result['connections'] = int(threads_connections_match.group(2))
    
    # Extracting latency details
    latency_match = re.search(r'Latency\s+([\d.]+ms)\s+([\d.]+us)\s+([\d.]+ms)', text)
    if latency_match:
        result['latency'] = {
            'avg': latency_match.group(1),
            'stdev': latency_match.group(2),
            'max': latency_match.group(3)
        }
    
    # Extracting Req/Sec details
    req_sec_match = re.search(r'Req/Sec\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', text)
    if req_sec_match:
        result['req_per_sec'] = {
            'avg': req_sec_match.group(1),
            'stdev': req_sec_match.group(2),
            'max': req_sec_match.group(3)
        }

    # Extracting request and data transfer details
    requests_match = re.search(r'(\d+) requests in ([\d.]+)s, ([\d.]+MB) read', text)
    if requests_match:
        result['total_requests'] = int(requests_match.group(1))
        result['total_duration'] = float(requests_match.group(2))
        result['data_read'] = requests_match.group(3)

    # Extracting requests/sec and transfer/sec details
    req_sec_final_match = re.search(r'Requests/sec:\s+([\d.]+)', text)
    transfer_sec_match = re.search(r'Transfer/sec:\s+([\d.]+KB)', text)
    
    if req_sec_final_match:
        result['requests_per_sec'] = float(req_sec_final_match.group(1))
    
    if transfer_sec_match:
        result['transfer_per_sec'] = transfer_sec_match.group(1)
    
    return result

def run_benchmark(frameworks, endpoints, duration='30s', threads=2, connections=10, output_dir='results'):
    """
    Run benchmarking for multiple frameworks and endpoints.

    Args:
        frameworks (dict): Dictionary of framework names and their base URLs.
        endpoints (list): List of endpoints to benchmark.
        duration (str): Duration of the test.
        threads (int): Number of threads to use.
        connections (int): Number of connections to use.
        output_dir (str): Directory to store the JSON results.

    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for framework, base_url in frameworks.items():
        framework_results = {}
        
        for endpoint in endpoints:
            url = f'{base_url}/{endpoint}'
            print(f'Running wrk for {framework} on {url}')
            
            result = run_wrk(url, duration, threads, connections)
            framework_results[endpoint] = result
            
        output_file = os.path.join(output_dir, f'{framework}_results.json')
        with open(output_file, 'w') as f:
            json.dump(framework_results, f, indent=4)
        
        print(f'Results saved to {output_file}')

# Example usage
if __name__ == '__main__':
    
    print("Enter Base URLs example : http://localhost:8000 ")
    django_base_url = input("Please enter url for django \n")
    fastapi_base_url = input("Please enter url for fastapi \n")
    flask_base_url = input("Please enter url for flask \n")
    express_base_url = input("Please enter url for express \n")
    fastify_base_url = input("Please enter url for fastify \n")
    gin_gorm_base_url = input("Please enter url for gin-gorm \n")

    frameworks = {}

    if django_base_url:
        frameworks["django"] = django_base_url
    if fastapi_base_url:
        frameworks['fastapi'] = fastapi_base_url
    if flask_base_url:
        frameworks['flask'] = flask_base_url
    if express_base_url:
        frameworks['express'] = express_base_url
    if fastify_base_url:
        frameworks['fastify'] = fastify_base_url
    if gin_gorm_base_url:
        frameworks['gin'] = gin_gorm_base_url

    queries = input("Enter Queries you want to make for multiple queries and updates \n")
    endpoints = [
        'json',
        'plaintext',
        'fortunes',
        'db',
        f'dbs?queries={queries}',
        f'updates?queries={queries}',
    ]
    
    run_benchmark(frameworks, endpoints, duration='30s', threads=2, connections=10)
