#!/usr/bin/env python3
"""Inspect IAM role policies and explicit AssumeRole links.

This is an inventory/debugging tool, not a full effective-permissions engine.
Effective access can also depend on explicit denies, SCPs, permission
boundaries, resource policies, session policies, tags, and conditions.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


class IAMRoleAnalyzer:
    def __init__(self) -> None:
        import boto3

        self.iam = boto3.client("iam")
        self.seen_roles: set[str] = set()

    def role_name_from_arn(self, role_arn: str) -> str:
        return role_arn.rsplit("/", 1)[-1]

    def get_role_policies(self, role_name: str) -> list[dict[str, Any]]:
        policies: list[dict[str, Any]] = []

        for policy_name in self.iam.list_role_policies(RoleName=role_name)[
            "PolicyNames"
        ]:
            response = self.iam.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
            )
            policies.append(
                {
                    "type": "inline",
                    "name": policy_name,
                    "document": response["PolicyDocument"],
                }
            )

        attached = self.iam.list_attached_role_policies(RoleName=role_name)[
            "AttachedPolicies"
        ]
        for policy in attached:
            policy_arn = policy["PolicyArn"]
            metadata = self.iam.get_policy(PolicyArn=policy_arn)["Policy"]
            version = self.iam.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=metadata["DefaultVersionId"],
            )["PolicyVersion"]
            policies.append(
                {
                    "type": "managed",
                    "name": policy["PolicyName"],
                    "arn": policy_arn,
                    "document": version["Document"],
                }
            )

        return policies

    def analyze_role(self, role_arn: str) -> dict[str, Any]:
        if role_arn in self.seen_roles:
            return {"role_arn": role_arn, "already_seen": True}

        self.seen_roles.add(role_arn)
        role_name = self.role_name_from_arn(role_arn)
        policies = self.get_role_policies(role_name)

        actions: set[str] = set()
        resources: set[str] = set()
        assumable_roles: set[str] = set()

        for policy in policies:
            for statement in as_list(policy["document"].get("Statement", [])):
                if statement.get("Effect") != "Allow":
                    continue

                statement_actions = as_list(statement.get("Action", []))
                statement_resources = as_list(statement.get("Resource", []))
                actions.update(statement_actions)
                resources.update(statement_resources)

                if "sts:AssumeRole" in statement_actions or "*" in statement_actions:
                    for resource in statement_resources:
                        if isinstance(resource, str) and ":role/" in resource:
                            assumable_roles.add(resource)

        return {
            "role_arn": role_arn,
            "policies": policies,
            "allowed_actions": sorted(actions),
            "allowed_resources": sorted(resources),
            "assumable_roles": sorted(assumable_roles),
            "assumable_role_details": [
                self.safe_analyze_role(arn) for arn in sorted(assumable_roles)
            ],
        }

    def safe_analyze_role(self, role_arn: str) -> dict[str, Any]:
        from botocore.exceptions import ClientError

        try:
            return self.analyze_role(role_arn)
        except ClientError as exc:
            return {"role_arn": role_arn, "error": str(exc)}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect IAM role policies.")
    parser.add_argument("role_arn")
    args = parser.parse_args()

    analyzer = IAMRoleAnalyzer()
    print(json.dumps(analyzer.safe_analyze_role(args.role_arn), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
