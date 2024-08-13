import subprocess
import json
import os

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

def parse_wrk_output(output):
    """
    Parse the output from wrk into a dictionary format.

    Args:
        output (str): The output from wrk command.

    Returns:
        dict: Parsed output with relevant data.
    """
    lines = output.splitlines()
    data = {}
    
    for line in lines:
        if 'Requests/sec:' in line:
            data['requests_per_sec'] = float(line.split(': ')[1].strip())
        elif 'Latency' in line:
            data['latency'] = line.split(': ')[1].strip()
        elif 'Socket errors' in line:
            errors = line.split(': ')[1].strip().split(', ')
            for error in errors:
                key, value = error.split(' ')
                data[key.lower() + '_errors'] = int(value)
        elif 'Transfer/sec:' in line:
            data['transfer_per_sec'] = line.split(': ')[1].strip()
    
    return data

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
    frameworks = {
        'fastapi': 'http://localhost:8000',
        'django': 'http://localhost:8001',
        'flask': 'http://localhost:8002',
        'express': 'http://localhost:8003'
    }
    
    endpoints = [
        'api/v1/resource',
        'api/v1/another-resource',
    ]
    
    run_benchmark(frameworks, endpoints, duration='30s', threads=4, connections=20)
