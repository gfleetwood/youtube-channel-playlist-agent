import os
from config import TO_EMAIL
from datetime import datetime
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartHyperAgentTaskParams
from functions import rec_read, rec_create, rec_update, rec_delete, extract_and_parse_dict, send_email
from jinja2 import Template

CLIENT = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))
DB = "/etc/secrets/tasks.rec"
REC_TYPE = "Task"

if __name__ == "__main__":

    tasks = []

    for task in rec_read(DB, REC_TYPE):
        prompt = Template(task['Prompt']).render(URL=task['URL'], time_stamp=task['LastRun'])
        tasks.append({"task": task, "prompt": prompt})

    for item in tasks:

        now = datetime.now()
        prompt = item["prompt"]
        print(prompt)

        result = CLIENT.agents.hyper_agent.start_and_wait(
            params=StartHyperAgentTaskParams(
                version="1.1.0",
                task=prompt,
                llm="gpt-4.1-mini",
                max_steps=100,
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "duration": {"type": "string"},
                    },
                    "required": ["title", "url", "duration"],
                }
            )
        )

        print(result.data.final_result)
        send_email(TO_EMAIL, item['task']['Name'], result.data.final_result)
        rec_update(DB, REC_TYPE, f"Name = '{item['task']['Name']}'", LastRun=now.strftime('%Y-%m-%d %H:%M:%S'))