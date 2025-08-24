from graph import graph
import json

def run_agent():
    task = input("What would you like your essay to be about? ")
    max_revisions = int(input("How many revisions would you like to allow? "))

    thread = {
        "configurable": {
            "thread_id": 1
        }
    }

    initial_state = {
        "task": task,
        "plan": "",
        "draft": "",
        "critique": "",
        "content": [],
        "revision_number": 1,
        "max_revisions": max_revisions
    }

    for stream in graph.stream(initial_state, thread):
        try:
            print(json.dumps(stream, indent=2))
        except TypeError:
            if hasattr(stream, '__dict__'):
                print(json.dumps(stream.__dict__, indent=2))
            else:
                print(str(stream))
