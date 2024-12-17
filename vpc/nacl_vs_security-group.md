# NACL and Security Groups

1. Key Differences between NACL and Security Groups:

NACL (Network Access Control List):

- Works at subnet level (all resources in a subnet)
- Stateless - must explicitly allow both inbound AND outbound rules
- Rules are processed in order (rule number priority)
- Can explicitly ALLOW and DENY rules
- One NACL per subnet, but a NACL can be associated with multiple subnets

Security Groups:

- Works at instance level (individual EC2, RDS, etc.)
- Stateful - if you allow inbound traffic, the response is automatically allowed out
- All rules are evaluated before deciding
- Can only specify ALLOW rules (implicit deny)
- Multiple security groups can be attached to one instance

2. Usage Scenarios:

Use Security Groups when:

- You need instance-level control
- Your requirements are simple "allow" rules
- You want automatic handling of return traffic
- You're managing individual applications/services
  Example: Running different web applications on different ports on same EC2

Use NACLs when:

- You need subnet-wide protection
- You specifically need to DENY certain IPs/traffic
- You want an additional security layer
- You need to block specific malicious IPs
  Example: Blocking known malicious IP ranges across entire subnet

3. NACL vs Security Group Priority:

- They don't override each other - they work together
- Traffic must pass BOTH to reach your instance
- Order: Internet → NACL → Security Group → Instance

4. **Making your webserver accessible:**

A) From your on-premise PC:

```plaintext
1. Security Group Configuration:
- Add inbound rule:
  Type: Custom TCP
  Port: 5000
  Source: Your on-premise IP address

2. NACL Configuration (if using custom NACL):
- Add inbound rule:
  Rule #: 100 (or any number)
  Type: Custom TCP
  Port: 5000
  Source: Your on-premise IP address
  Allow/Deny: ALLOW
- Add outbound rule:
  Rule #: 100
  Type: Custom TCP
  Port: ephemeral (32768-65535)
  Destination: Your on-premise IP address
  Allow/Deny: ALLOW
```

B) From the Internet:

```plaintext
1. Security Group Configuration:
- Add inbound rule:
  Type: Custom TCP
  Port: 5000
  Source: 0.0.0.0/0 (all IPs)

2. NACL Configuration (if using custom NACL):
- Add inbound rule:
  Rule #: 100
  Type: Custom TCP
  Port: 5000
  Source: 0.0.0.0/0
  Allow/Deny: ALLOW
- Add outbound rule:
  Rule #: 100
  Type: Custom TCP
  Port: ephemeral (32768-65535)
  Destination: 0.0.0.0/0
  Allow/Deny: ALLOW
```

Best Practices:

1. For internet-facing applications, always use both NACL and Security Groups
2. Use Security Groups as your primary access control
3. Use NACLs as a backup security layer
4. Always follow the principle of least privilege
5. For internet access, consider using AWS ALB/NLB instead of direct access
6. Regularly audit and update your rules
