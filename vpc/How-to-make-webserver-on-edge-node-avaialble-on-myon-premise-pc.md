# Making your webserver accessible on aws edge node from an on premise pc/server

A) **For you aws edge-node add:**

<pre class="code-fence" md-src-pos="1534..2006"><div class="code-fence-highlighter-copy-button" data-fence-content="MS4gU2VjdXJpdHkgR3JvdXAgQ29uZmlndXJhdGlvbjoKLSBBZGQgaW5ib3VuZCBydWxlOgogIFR5cGU6IEN1c3RvbSBUQ1AKICBQb3J0OiA1MDAwCiAgU291cmNlOiBZb3VyIG9uLXByZW1pc2UgSVAgYWRkcmVzcwoKMi4gTkFDTCBDb25maWd1cmF0aW9uIChpZiB1c2luZyBjdXN0b20gTkFDTCk6Ci0gQWRkIGluYm91bmQgcnVsZToKICBSdWxlICM6IDEwMCAob3IgYW55IG51bWJlcikKICBUeXBlOiBDdXN0b20gVENQCiAgUG9ydDogNTAwMAogIFNvdXJjZTogWW91ciBvbi1wcmVtaXNlIElQIGFkZHJlc3MKICBBbGxvdy9EZW55OiBBTExPVwotIEFkZCBvdXRib3VuZCBydWxlOgogIFJ1bGUgIzogMTAwCiAgVHlwZTogQ3VzdG9tIFRDUAogIFBvcnQ6IGVwaGVtZXJhbCAoMzI3NjgtNjU1MzUpCiAgRGVzdGluYXRpb246IFlvdXIgb24tcHJlbWlzZSBJUCBhZGRyZXNzCiAgQWxsb3cvRGVueTogQUxMT1c="><img class="code-fence-highlighter-copy-button-icon" data-original-src="vpc" src="http://localhost:63342/markdownPreview/1139199909/vpc?_ijt=c83u7f0o829dhv46iq2tith5n3"/><span class="tooltiptext"></span></div><code class="language-plaintext" md-src-pos="1534..2006"><span md-src-pos="1534..1547"></span><span md-src-pos="1547..1580">1. Security Group Configuration:
</span><span md-src-pos="1580..1600">- Add inbound rule:
</span><span md-src-pos="1600..1619">  Type: Custom TCP
</span><span md-src-pos="1619..1632">  Port: 5000
</span><span md-src-pos="1632..1669">  Source: Your on-premise IP address
</span><span md-src-pos="1669..1670">
</span><span md-src-pos="1670..1716">2. NACL Configuration (if using custom NACL):
</span><span md-src-pos="1716..1736">- Add inbound rule:
</span><span md-src-pos="1736..1766">  Rule #: 100 (or any number)
</span><span md-src-pos="1766..1785">  Type: Custom TCP
</span><span md-src-pos="1785..1798">  Port: 5000
</span><span md-src-pos="1798..1835">  Source: Your on-premise IP address
</span><span md-src-pos="1835..1855">  Allow/Deny: ALLOW
</span><span md-src-pos="1855..1876">- Add outbound rule:
</span><span md-src-pos="1876..1890">  Rule #: 100
</span><span md-src-pos="1890..1909">  Type: Custom TCP
</span><span md-src-pos="1909..1941">  Port: ephemeral (32768-65535)
</span><span md-src-pos="1941..1983">  Destination: Your on-premise IP address
</span><span md-src-pos="1983..2003">  Allow/Deny: ALLOW</span></code></pre>


B. **Using port forwarding!**

1. SSH Port Forwarding Options:

```bash
# Local port forwarding (most common for your case)
ssh -L 8080:localhost:5000 user@edge-node-ip

# This maps your local port 8080 to edge node's port 5000
# After running this, access the web server via: http://localhost:8080
```

2. Different Types of Port Forwarding:

- Local (-L): Forward local port to remote server

  ```bash
  ssh -L local_port:remote_host:remote_port user@server
  ```
- Remote (-R): Forward remote port to local machine

  ```bash
  ssh -R remote_port:local_host:local_port user@server
  ```
- Dynamic (-D): Creates SOCKS proxy

  ```bash
  ssh -D local_port user@server
  ```

For your specific case (web server on port 5000):

1. Simplest Solution:

```bash
ssh -L 8080:localhost:5000 user@edge-node-ip -N
```

The `-N` flag means "don't execute remote commands" - useful for just port forwarding

Benefits of this approach:

- No need to modify security groups for port 5000
- Traffic is encrypted through SSH tunnel
- Only need SSH port (22) open on AWS
- Can work through corporate firewalls that block other ports

C. **And avoid entering the password by setting up SSH key-based authentication.**

1. Generate SSH key pair on your local machine (if you haven't already):

```bash
# Generate key pair
ssh-keygen -t rsa -b 2048
# Press enter to save in default location (~/.ssh/id_rsa)
# Optionally enter passphrase (or press enter for no passphrase)
```

2. Copy your public key to the edge node:

```bash
# Method 1: Using ssh-copy-id (easiest)
ssh-copy-id user@edge-node-ip

# Method 2: Manual copy (if ssh-copy-id isn't available)
cat ~/.ssh/id_rsa.pub | ssh user@edge-node-ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

3. Now you can use port forwarding without password:

```bash
ssh -L 8080:localhost:5000 user@edge-node-ip -N
```

To make it even more convenient:

4. Add an entry to your SSH config (~/.ssh/config):

```bash
Host edgenode
    HostName edge-node-ip
    User your-username
    IdentityFile ~/.ssh/id_rsa
```

Then you can simply use:

```bash
ssh -L 8080:localhost:5000 edgenode -N
```

Would you like me to explain any of these steps in more detail?
