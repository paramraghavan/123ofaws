Create a Python script using boto3 to recursively list IAM roles, their assumed roles, and analyze their
permissions.

```python
import boto3
import json
from botocore.exceptions import ClientError
from typing import Dict, List, Set


class IAMRoleAnalyzer:
    def __init__(self):
        self.iam_client = boto3.client('iam')
        self.analyzed_roles = set()

    def get_role_policies(self, role_name: str) -> List[Dict]:
        """Get both inline and managed policies attached to a role."""
        policies = []

        # Get inline policies
        try:
            inline_policies = self.iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
            for policy_name in inline_policies:
                policy = self.iam_client.get_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name
                )
                policies.append({
                    'PolicyName': policy_name,
                    'PolicyDocument': policy['PolicyDocument'],
                    'Type': 'Inline'
                })
        except ClientError as e:
            print(f"Error getting inline policies for role {role_name}: {e}")

        # Get attached managed policies
        try:
            attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
            for policy in attached_policies:
                policy_arn = policy['PolicyArn']
                policy_version = self.iam_client.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
                policy_document = self.iam_client.get_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy_version
                )['PolicyVersion']['Document']

                policies.append({
                    'PolicyName': policy['PolicyName'],
                    'PolicyArn': policy_arn,
                    'PolicyDocument': policy_document,
                    'Type': 'Managed'
                })
        except ClientError as e:
            print(f"Error getting managed policies for role {role_name}: {e}")

        return policies

    def extract_assumed_roles(self, policy_document: Dict) -> Set[str]:
        """Extract AssumeRole ARNs from policy document."""
        assumed_roles = set()

        def process_statement(statement):
            if isinstance(statement, dict):
                action = statement.get('Action', [])
                actions = [action] if isinstance(action, str) else action

                resource = statement.get('Resource', [])
                resources = [resource] if isinstance(resource, str) else resource

                if 'sts:AssumeRole' in actions:
                    assumed_roles.update([r for r in resources if r.startswith('arn:aws:iam:')])

        statements = policy_document.get('Statement', [])
        if isinstance(statements, list):
            for statement in statements:
                process_statement(statement)
        else:
            process_statement(statements)

        return assumed_roles

    def analyze_role_permissions(self, role_arn: str) -> Dict:
        """Recursively analyze role and its assumed roles."""
        if role_arn in self.analyzed_roles:
            return {}

        self.analyzed_roles.add(role_arn)
        role_name = role_arn.split('/')[-1]

        try:
            role_info = {
                'RoleArn': role_arn,
                'Policies': [],
                'AssumedRoles': [],
                'Permissions': set(),
                'Resources': set()
            }

            # Get role policies
            policies = self.get_role_policies(role_name)
            role_info['Policies'] = policies

            # Extract permissions and resources
            for policy in policies:
                policy_doc = policy['PolicyDocument']
                statements = policy_doc.get('Statement', [])
                if not isinstance(statements, list):
                    statements = [statements]

                for statement in statements:
                    if statement.get('Effect') == 'Allow':
                        actions = statement.get('Action', [])
                        if isinstance(actions, str):
                            actions = [actions]
                        role_info['Permissions'].update(actions)

                        resources = statement.get('Resource', [])
                        if isinstance(resources, str):
                            resources = [resources]
                        role_info['Resources'].update(resources)

                # Find assumed roles
                assumed_roles = self.extract_assumed_roles(policy_doc)
                for assumed_role in assumed_roles:
                    if assumed_role not in self.analyzed_roles:
                        assumed_role_info = self.analyze_role_permissions(assumed_role)
                        if assumed_role_info:
                            role_info['AssumedRoles'].append(assumed_role_info)
                            role_info['Permissions'].update(assumed_role_info.get('Permissions', set()))
                            role_info['Resources'].update(assumed_role_info.get('Resources', set()))

            # Convert sets to lists for JSON serialization
            role_info['Permissions'] = sorted(list(role_info['Permissions']))
            role_info['Resources'] = sorted(list(role_info['Resources']))

            return role_info

        except ClientError as e:
            print(f"Error analyzing role {role_arn}: {e}")
            return {}


def analyze_iam_role(role_arn: str) -> None:
    """Main function to analyze an IAM role and its permissions."""
    analyzer = IAMRoleAnalyzer()
    role_analysis = analyzer.analyze_role_permissions(role_arn)

    # Pretty print the results
    print(json.dumps(role_analysis, indent=2))


# Example usage
if __name__ == "__main__":
    role_arn = "arn:aws:iam::123456789012:role/example-role"
    analyze_iam_role(role_arn)

```

Above script provides a comprehensive analysis of IAM roles and their permissions. 
Let me explain:

1. Creates an `IAMRoleAnalyzer` class that handles:
    - Fetching both inline and managed policies
    - Extracting assumed roles from policy documents
    - Recursively analyzing permissions for assumed roles
    - Collecting all permissions and resources

2. For each role, it gathers:
    - Role ARN
    - All attached policies (both inline and managed)
    - List of assumed roles
    - Consolidated list of permissions
    - Consolidated list of resources

3. Key features:
    - Handles both inline and managed policies
    - Recursively analyzes assumed roles
    - Prevents infinite loops by tracking analyzed roles
    - Handles AWS API errors gracefully
    - Provides detailed output in JSON format

To use the script:

```python
role_arn = "arn:aws:iam::123456789012:role/your-role-name"
analyze_iam_role(role_arn)
```
