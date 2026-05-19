Yes, you can absolutely do this with the Apptio Cloudability REST API.

If you have the Cloudability Kubernetes agent installed on your EKS cluster, Cloudability tracks allocated vs.
unallocated (idle) resources. You can query their **v3 Reporting API** to aggregate this data and build a "Leaderboard
of Waste" showing the namespaces burning the most money on idle resources.

Here is a Python script that connects to the Cloudability `v3/reporting/cost/run` endpoint, groups the data by
Kubernetes namespace, sorts it by idle cost in descending order, and limits it to the top 10.

### The Cloudability API Python Script

**Prerequisites:** You will need an API key from your Cloudability account (found under **Settings > Preferences > API
Key**).

```python
import requests
import datetime
import base64

# --- Configuration ---
# Replace with your actual Cloudability API Key
API_KEY = "your_cloudability_api_key_here"
BASE_URL = "https://api.cloudability.com/v3"


def get_idle_namespaces_leaderboard():
    # Look back over the last 7 days to get a solid baseline
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=7)

    # Cloudability Reporting Endpoint
    endpoint = f"{BASE_URL}/reporting/cost/run"

    # Define what we want to ask the Cloudability engine
    # Note: Depending on your exact Cloudability configuration, the waste metric
    # might be named 'unallocated_cost', 'idle_cost', or 'kubernetes_idle_cost'.
    target_metric = "unallocated_cost"

    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "dimensions": "kubernetes_namespace",
        "metrics": target_metric,
        "order": "desc",
        "sort_by": target_metric,
        "limit": 15  # Pulling 15 so we can filter out system namespaces and still get 10
    }

    # Cloudability expects Basic Auth using the API key as the username and an empty password
    auth_string = f"{API_KEY}:"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Accept": "application/json"
    }

    try:
        print(f"Fetching Cloudability report from {start_date} to {end_date}...\n")
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            print("No idle Kubernetes resources found. (Check if the Cloudability metrics agent is reporting).")
            return

        # --- Print the Leaderboard ---
        print("🏆 TOP 10 IDLE NAMESPACES LEADERBOARD (Last 7 Days) 🏆")
        print("=" * 65)
        print(f"{'NAMESPACE':<40} | {'WASTED SPEND'}")
        print("-" * 65)

        count = 0
        for item in results:
            # Stop if we've printed our top 10
            if count >= 10:
                break

            namespace = item.get("kubernetes_namespace", "Unknown")
            idle_cost = float(item.get(target_metric, 0.0))

            # Filter out standard system namespaces that are naturally running
            if namespace in ['kube-system', 'cloudability', 'default']:
                continue

            print(f"{namespace:<40} | ${idle_cost:,.2f}")
            count += 1

        print("=" * 65)

    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        # Print out the exact error from Cloudability if available
        if hasattr(e, 'response') and e.response is not None:
            print(f"Details: {e.response.text}")


if __name__ == "__main__":
    get_idle_namespaces_leaderboard()

```

### Key Things to Keep in Mind for Cloudability:

* **API Authentication:** Cloudability uses Basic Auth, but interestingly, they use your API key as the *username* with
  a blank password. The script handles this encoding automatically.
* **Metric Naming:** Apptio updates its API taxonomy occasionally. In most modern setups using their Advanced Containers
  module, the metric for waste is `unallocated_cost` or `idle_cost`. If the script returns an error saying the metric
  doesn't exist, check your Cloudability UI under "Metrics" to see exactly what they have named the container idle
  metric in your tenant.
* **Agent Requirement:** This will only return data if you have the IBM/Apptio FinOps Agent deployed on your EKS cluster
  pushing metrics back to Cloudability. Without the agent, Cloudability only knows the cost of the underlying EC2 nodes,
  not how the pods inside are behaving.