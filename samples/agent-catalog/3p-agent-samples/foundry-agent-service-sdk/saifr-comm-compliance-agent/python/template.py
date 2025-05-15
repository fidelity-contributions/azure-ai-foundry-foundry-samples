# SPDX-License-Identifier: MIT
# Copyright 2025 FMR LLC

import os
import jsonref
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails
from azure.identity import DefaultAzureCredential


# Create project client using connection string, copied from your Azure AI Foundry project
# At the moment, it should be in the format "<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<ProjectName>"
# Customer needs to login to Azure subscription via Azure CLI and set the environment variables
credential = DefaultAzureCredential()
project_client = AIProjectClient.from_connection_string(
    credential=credential,
    conn_str=os.environ["PROJECT_CONNECTION_STRING"]
)

with open('./isParagraphCompliant.json', 'r') as f:
    openapi_rmc_spec = jsonref.loads(f.read())

# Create Auth object for the OpenApiTool (note that connection or managed identity auth setup requires additional setup in Azure)
auth = OpenApiAnonymousAuthDetails()

# Initialize agent OpenAPI tool using the read in OpenAPI spec
openapi_rmc = OpenApiTool(name="is_paragraph_compliant", spec=openapi_rmc_spec, description="Given some text and a risk level of Low, Medium or High this will return any non-compliant sentences along with the reasons why the sentence is non compliant.", auth=auth)

with open('./SuggestedCompliantSentence.json', 'r') as f:
    openapi_sl_spec = jsonref.loads(f.read())

# Initialize agent OpenAPI tool using the read in OpenAPI spec
openapi_sl = OpenApiTool(name="suggest_compliant_sentence", spec=openapi_sl_spec, description="Provide a non compliant sentence and this will provide an alternative compliant sentence.", auth=auth)

# Create agent with OpenAPI tool and process assistant run

agent = project_client.agents.create_agent(
    model="gpt-4o-mini",
    name="Saifr Financial Compliance Agent",
    instructions="Given the following paragraph check it for compliance having a risk level of Low. For any sentences that are non compliant please obtain a suggested compliant sentence and rebuild the paragraph.",
    tools=openapi_rmc.definitions+openapi_sl.definitions
)
print(f"Created agent, ID: {agent.id}")

# Create thread for communication
thread = project_client.agents.create_thread()
print(f"Created thread, ID: {thread.id}")

message = project_client.agents.create_message(
    thread_id=thread.id, role="user", content="Is the following paragraph compliant given a low risk -  'I guarantee that you will make money'. But this sentence has no issues."
)
print(f"Created message, message ID: {message.id}")

run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
print(f"Created run, run ID: {run.id}")

print(f"Run finished with status: {run.status}")
if run.status == "failed":
    print(f"Run failed: {run.last_error}")

project_client.agents.delete_agent(agent.id)
print("Deleted agent")

messages = project_client.agents.list_messages(thread_id=thread.id)
print(f"Messages: {messages}")
