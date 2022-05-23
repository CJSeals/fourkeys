# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import base64
import shared
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    """
    Receives messages from a push subscription from Pub/Sub.
    Parses the message, and inserts it into BigQuery.
    """
    event = None

    # Check request for JSON
    if not request.is_json:
        raise Exception("Expecting JSON payload")

    envelope = request.get_json()

    # Check that message is a valid pub/sub message
    if "message" not in envelope:
        raise Exception("Not a valid Pub/Sub Message")

    msg = envelope["message"]

    try:
        event = process_azure_devops_event(msg)
        if event:
            shared.insert_row_into_bigquery(event) # [Do not edit]

    except Exception as e:
        entry = {
            "errors":       str(e),
            "severity":     "WARNING",
            "json_payload": envelope,
            "msg":          "Data not saved to BigQuery"
        }

        print(json.dumps(entry))

    return "", 204

def process_azure_devops_event(msg):
    supportedEventTypes = {
        "git.push",                                  # Push to Master
        "git.pullrequest.merged",                    # Merge to Master
        "ms.vss-pipelines.run-state-changed-event"   # Using as Temporary Deployment Event
    }

    signature   = shared.create_unique_id(msg)
    metadata    = json.loads(base64.b64decode(msg["data"]).decode("utf-8").strip())

    # Verify Incoming Event is Supported
    event_type = metadata["eventType"]
    if event_type not in supportedEventTypes:
        raise Warning("Unsupported Azure Devops Event: '%s'" % event_type)

    # Fill Raw Event Record Data
    new_source_event = {
        "signature":    signature,                  # The unique event signature
        "event_type":   event_type,                 # Event type, eg "push", "pull_reqest", etc
        "id":           metadata["id"],             # Object ID, eg pull request ID
        "source":       "azure-devops",             # The name of the source, eg "github"
        "msg_id":       msg["message_id"],          # The pubsub message id
        "metadata":     json.dumps(metadata),       # The body of the msg
        "time_created": metadata["createdDate"],    # The timestamp of with the event
    }

    return new_source_event

if __name__ == "__main__":
    PORT = int(os.getenv("PORT")) if os.getenv("PORT") else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host="127.0.0.1", port=PORT, debug=True)