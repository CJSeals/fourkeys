# Copyright 2020 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import main
import json
import mock
import pytest
import base64
import shared

@pytest.fixture
def client():
    main.app.testing = True
    return main.app.test_client()

def test_not_json(client):
    with pytest.raises(Exception) as e:
        client.post("/", data="foo")

    assert "Expecting JSON payload" in str(e.value)

def test_not_pubsub_message(client):
    with pytest.raises(Exception) as e:
        client.post(
            "/",
            data=json.dumps({"foo": "bar"}),
            headers={"Content-Type": "application/json"},
        )

    assert "Not a valid Pub/Sub Message" in str(e.value)

def test_azure_devops_source_event_processssed(client):
    pubsub_msg = {
        #TODO: ADD TEST MESSAGE FOLLOWING AZURE DEVOPS MESSAGE FORMAT
    }

    event = {
        "event_type": "event_type",
        "id": "e_id",
        "metadata": '{"foo": "bar"}',
        "time_created": 0,
        "signature": "signature",
        "msg_id": "foobar",
        "source": "source",
    }

    shared.insert_row_into_bigquery = mock.MagicMock()

    r = client.post(
        "/",
        data=json.dumps(pubsub_msg),
        headers={"Content-Type": "application/json"},
    )

    shared.insert_row_into_bigquery.assert_called_with(event)
    assert r.status_code == 204