To run the setup.py file for your s3-sql package, you have several options depending on your intended goal. Here's how
to use it for different purposes:

## Installing the Package in Development Mode

If you're actively developing the package and want to test changes without reinstalling:

```bash
# Navigate to the directory containing setup.py
cd path/to/s3-sql

# Install in development mode
pip install -e .
```

This creates a link to your source code instead of copying files, so changes to the code take effect immediately without
reinstallation.

## Building the Package

If you want to build a distributable package:

```bash
# Install build tools if needed
pip install build

# Build the package
python -m build
```

This will create distribution files in the `dist/` directory:

- A source distribution (.tar.gz file)
- A wheel distribution (.whl file)

## Installing the Package Locally

To install the package normally on your system:

```bash
# Navigate to the directory containing setup.py
cd path/to/s3-sql

# Install directly
pip install .
```

## Creating a Package for Distribution

If you want to share your package with others via PyPI:

```bash
# Install required tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI (requires PyPI account)
twine upload dist/*
```

## Common Issues and Tips

1. Make sure your directory structure is correct:
   ```
   s3-sql/
   ├── s3_sql/
   │   ├── __init__.py
   │   └── s3_sql.py
   ├── setup.py
   └── README.md
   ```

2. The `__init__.py` file in the s3_sql directory should import your main class:
   ```python
   from .s3_sql import S3DataManager
   ```

3. If you get any errors about missing dependencies, make sure they're listed in the `install_requires` section of
   setup.py.

