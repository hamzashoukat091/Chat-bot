import json
import boto3
text1 = "How cute your dog is!"
text2 = "Your dog is so cute."
text3 = "The mitochondria is the powerhouse of the cell."
endpoint_name = 'e5-large-embedding'

def query_endpoint(encoded_json, content_type):
    client = boto3.client('runtime.sagemaker')
    response = client.invoke_endpoint(EndpointName=endpoint_name, ContentType=content_type, Body=encoded_json)
    return json.loads(response['Body'].read())


payload = [text1, text2, text3]
query_response = query_endpoint(json.dumps(payload).encode('utf-8'), 'application/x-text')
#It will output the embeddings for the input data list
print(len(query_response['embedding'][0]))
corpus =  ["Amazon SageMaker is a fully managed service to prepare data and build, train, and deploy machine learning (ML) models for any use case with fully managed infrastructure, tools, and workflows.",
"Amazon SageMaker stores code in ML storage volumes, secured by security groups and optionally encrypted at rest.",
"Amazon SageMaker provides a full end-to-end workflow, but you can continue to use your existing tools with SageMaker. You can easily transfer the results of each stage in and out of SageMaker as your business requirements dictate."]
queries = ["What is Amazon SageMaker?", "How does Amazon SageMaker secure my code?", "What if I have my own notebook, training, or hosting environment?"]

payload_nearest_neighbour = {"corpus": corpus, "queries": queries, "top_k": 3, "mode": "nn_corpus"}

query_response = query_endpoint(json.dumps(payload_nearest_neighbour).encode('utf-8'), 'application/json')
print(query_response)