import json
import boto3

endpoint_name = "llama2-13b-chat"


def query_endpoint(payload):
    client = boto3.client("sagemaker-runtime")
    response = client.invoke_endpoint(
        EndpointName=endpoint_name, InferenceComponentName='meta-textgeneration-llama-2-13b-f-20240225-081412',
        ContentType="application/json",
        Body=json.dumps(payload),
    )
    response = response["Body"].read().decode("utf8")
    response = json.loads(response)
    return response


from typing import Dict, List


def format_messages(messages: List[Dict[str, str]]) -> List[str]:
    """Format messages for Llama-2 chat models.

    The model only supports 'system', 'user' and 'assistant' roles, starting with 'system', then 'user' and
    alternating (u/a/u/a/u...). The last message must be from 'user'.
    """
    prompt: List[str] = []

    if messages[0]["role"] == "system":
        content = "".join(["<<SYS>>\n", messages[0]["content"], "\n<</SYS>>\n\n", messages[1]["content"]])
        messages = [{"role": messages[1]["role"], "content": content}] + messages[2:]

    for user, answer in zip(messages[::2], messages[1::2]):
        prompt.extend(["<s>", "[INST] ", (user["content"]).strip(), " [/INST] ", (answer["content"]).strip(), "</s>"])

    prompt.extend(["<s>", "[INST] ", (messages[-1]["content"]).strip(), " [/INST] "])

    return "".join(prompt)


def print_messages(prompt: str, response: str) -> None:
    bold, unbold = '\033[1m', '\033[0m'
    print(f"{bold}> Input{unbold}\n{prompt}\n\n{bold}> Output{unbold}\n{response[0]['generated_text']}\n")


dialog = [{"role": "user", "content": "what is the recipe of mayonnaise?"}]
prompt = format_messages(dialog)
payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256, "top_p": 0.9, "temperature": 0.6}}
response = query_endpoint(payload)
print_messages(prompt, response)
dialog = [
    {"role": "user", "content": "I am going to Paris, what should I see?"},
    {
        "role": "assistant",
        "content": """\
Paris, the capital of France, is known for its stunning architecture, art museums, historical landmarks, and romantic atmosphere. Here are some of the top attractions to see in Paris:

1. The Eiffel Tower: The iconic Eiffel Tower is one of the most recognizable landmarks in the world and offers breathtaking views of the city.
2. The Louvre Museum: The Louvre is one of the world's largest and most famous museums, housing an impressive collection of art and artifacts, including the Mona Lisa.
3. Notre-Dame Cathedral: This beautiful cathedral is one of the most famous landmarks in Paris and is known for its Gothic architecture and stunning stained glass windows.

These are just a few of the many attractions that Paris has to offer. With so much to see and do, it's no wonder that Paris is one of the most popular tourist destinations in the world.""",
    },
    {"role": "user", "content": "What is so great about #1?"},
]
prompt = format_messages(dialog)
payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256, "top_p": 0.9, "temperature": 0.6}}
response = query_endpoint(payload)
print_messages(prompt, response)
dialog = [
    {"role": "system", "content": "Always answer with Haiku"},
    {"role": "user", "content": "I am going to Paris, what should I see?"},
]
prompt = format_messages(dialog)
payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256, "top_p": 0.9, "temperature": 0.6}}
response = query_endpoint(payload)
print_messages(prompt, response)
dialog = [
    {"role": "system", "content": "Always answer with emojis"},
    {"role": "user", "content": "How to go from Beijing to NY?"},
]
prompt = format_messages(dialog)
payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256, "top_p": 0.9, "temperature": 0.6}}
response = query_endpoint(payload)
print_messages(prompt, response)