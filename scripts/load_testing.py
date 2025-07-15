# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Script to test bulk updates.

Example of execution:
python load_testing.py [index] [threads] [calls] [records_size] [token] [host]
python load_testing.py documents 10 10 1000 ABCD localhost:5000
"""

import json
import random
import sys
import threading

import requests
import urllib3
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UpdateThread(threading.Thread):
    """Thread updating records."""

    pids = []
    calls = 50
    locks = {}
    token = None
    index = "documents"
    host = "localhost:5000"

    def __init__(self, thread_number):
        """Init.

        param int thread_number: Thread assigned number.
        """
        threading.Thread.__init__(self)
        self.thread_number = thread_number
        self.headers = {
            "Authorization": f"Bearer {UpdateThread.token}",
            "Content-type": "application/json",
        }

    def run(self):
        """Execute command."""
        for index in range(0, UpdateThread.calls):
            pid = random.choice(UpdateThread.pids)

            # Create lock if not exists
            if not UpdateThread.locks.get(pid):
                UpdateThread.locks[pid] = threading.Lock()

            # Lock for PID
            UpdateThread.locks[pid].acquire()

            url = f"https://{UpdateThread.host}/api/{UpdateThread.index}/{pid}"

            try:
                response = requests.get(url, verify=False, headers=self.headers)

                if response.status_code != 200:
                    raise Exception(f"GET error {response.status_code}")

                def remove_calculated_properties(data):
                    """Remove calculated properties to avoid a 400 error.

                    :param dict data: Data to process.
                    """
                    for key in list(data):
                        if key.startswith("_"):
                            del data[key]
                        else:
                            if isinstance(data[key], list):
                                for item in data[key]:
                                    if isinstance(item, dict):
                                        remove_calculated_properties(item)

                            if isinstance(data[key], dict):
                                remove_calculated_properties(data[key])

                data = response.json()
                remove_calculated_properties(data)

                response = requests.put(
                    url,
                    verify=False,
                    headers=self.headers,
                    data=json.dumps(data["metadata"]),
                )

                if response.status_code != 200:
                    raise Exception(f"PUT error {response.status_code}")

                print(
                    f"Updated {url} in execution {index + 1} of thread "
                    f"{(self.thread_number + 1)}: Status {response.status_code}, "
                    f"Time {response.elapsed.total_seconds()}"
                )
            except Exception as exception:
                print(
                    f"Error during processing of {url} in execution {index} "
                    f"of thread {(self.thread_number + 1)}: {str(exception)}"
                )

            # Unlock
            UpdateThread.locks[pid].release()


def get_records_pids(index="documents", size=1000):
    """Get a list of records PIDs for the given index.

    :param str index: Index to search for records.
    :param int size: Number of records to return.
    """
    results = (
        Search(using=Elasticsearch(), index=index)[0:size]
        .source(includes=["pid"])
        .execute()
    )

    return [item["pid"] for item in results]


if __name__ == "__main__":
    INDEX = sys.argv[1] if len(sys.argv) > 1 else "documents"
    NUMBER_OF_THREADS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    CALLS_PER_THREAD = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    RECORDS_SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    TOKEN = sys.argv[5] if len(sys.argv) > 5 else None
    HOST = sys.argv[6] if len(sys.argv) > 6 else "localhost:5000"

    print()
    print(f"Index: {INDEX}")
    print(f"Number of threads: {NUMBER_OF_THREADS}")
    print(f"Calls per thread: {CALLS_PER_THREAD}")
    print(f"Records size: {RECORDS_SIZE}")
    print(f"Authentication token: {TOKEN}")
    print(f"Host: {HOST}")

    RESPONSE = input("\nIs that correct? [y/N]: ")

    if RESPONSE.lower() != "y":
        exit(0)

    print()

    UpdateThread.pids = get_records_pids(index=INDEX, size=RECORDS_SIZE)
    UpdateThread.calls = CALLS_PER_THREAD
    UpdateThread.token = TOKEN
    UpdateThread.index = INDEX
    UpdateThread.host = HOST

    for i in range(0, NUMBER_OF_THREADS):
        thread = UpdateThread(i)
        thread.start()
