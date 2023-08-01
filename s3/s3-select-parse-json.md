# Parsing json using S3 Select
``` python
def s3_select():
    client = boto3.client("s3")
    bucket = "test"
    key = "test.json"
    expression_type = "SQL"
    expression = """SELECT * FROM S3Object"""
    input_serialization = {'CompressionType': 'GZIP', "JSON": {"Type": "Document"}}
    output_serialization = {"JSON": {}}
    response = client.select_object_content(
        Bucket=bucket,
        Key=key,
        ExpressionType=expression_type,
        Expression=expression,
        InputSerialization=input_serialization,
        OutputSerialization=output_serialization
    )
    for event in response["Payload"]:
        print(event)
```
