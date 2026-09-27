# Install AWS CLI v2 on macOS

Install the official AWS CLI v2:

```bash
curl -fsSL https://awscli.amazonaws.com/v2/install.sh | bash
```

Verify:

```bash
which aws
aws --version
```

If `which aws` points to pyenv, for example:

```text
/Users/paramraghavan/.pyenv/shims/aws
```

then your shell is finding a Python-installed AWS CLI first. Put the official install location before pyenv in
`~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Reload:

```bash
source ~/.zshrc
hash -r
which aws
aws --version
```

Expected version prefix:

```text
aws-cli/2
```

Configure a base profile:

```bash
aws configure --profile base
```

Official docs: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>
