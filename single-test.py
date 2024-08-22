import requests
import time
import json

def test_api_response_times(frameworks:dict, paths):
    results = []
    for key , val in frameworks.items():
        for path in paths:
            url = f"{val}/{path}"
            start_time = time.time()
            try:
                response = requests.get(url)
                elapsed_time = time.time() - start_time
                results.append({
                    "framework": key,
                    "path": path,
                    "url": url,
                    "status_code": response.status_code,
                    "response_time": elapsed_time,
                    "content_length": len(response.content)
                })
            except requests.RequestException as e:
                results.append({
                    "framework": key,
                    "path": path,
                    "url": url,
                    "error": str(e)
                })
    return results

def main():
    print("Enter Base URLs example : http://localhost:8000 ")
    django_base_url = input("Please enter url for django \n")
    fastapi_base_url = input("Please enter url for fastapi \n")
    flask_base_url = input("Please enter url for flask \n")
    express_base_url = input("Please enter url for express \n")
    fastify_base_url = input("Please enter url for fastify \n")
    gin_gorm_base_url = input("Please enter url for gin-gorm \n")

    frameworks = {
        'django': django_base_url,
        'fastapi': fastapi_base_url,
        'flask': flask_base_url,
        'express': express_base_url,
        'fastify': fastify_base_url,
        'gin': gin_gorm_base_url,
    }

    queries = input("Enter Queries you want to make for multiple queries and updates \n")
    paths = [
        'json',
        'plaintext',
        'fortunes',
        'db',
        f'dbs?queries={queries}',
        f'updates?queries={queries}',
]
    results = test_api_response_times(frameworks, paths)
    
    # Output results in JSON format
    with open("api_test_results.json", "w") as file:
        json.dump(results, file, indent=4)
    
    print("Results saved to api_test_results.json")

if __name__ == "__main__":
    main()
