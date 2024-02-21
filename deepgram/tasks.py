import instructor

from datetime import datetime as time
from pydantic import BaseModel, Field
from typing import Iterable, List, Optional
from openai import OpenAI
from rich.console import Console


client = instructor.patch(OpenAI())


class ActionItem(BaseModel):
    slug: str = Field(..., description="compact short slug")
    title: str = Field(description="The title of the action item")
    chain_of_thought: str = Field(
        description="Short chain of thought that led to this action item, specifically think about whether or not a task should be marked as completed"
    )
    is_completed: Optional[bool] = Field(
        False, description="Whether the action item is completed"
    )
    last_updated: Optional[str] = Field(
        default_factory=time.now().isoformat,
        description="Leave this null if you are an LLM, The date the action item was last updated",
    )


class ActionItemResponse(BaseModel):
    action_items: Optional[List[ActionItem]] = Field(
        ..., title="The list of action items"
    )

    def patch(self, action_item: ActionItem):
        current_items = {item.slug: item for item in self.action_items}
        current_items[action_item.slug] = action_item
        new_response = ActionItemResponse(action_items=list(current_items.values()))
        return new_response

    def __rich_console__(self, console: Console, options: dict):
        from rich.table import Table

        table = Table(
            title="Action Items (Realtime Updates)",
            show_header=True,
            caption="Start speaking to update the action items.",
        )
        table.add_column("Status")
        table.add_column("Title")
        table.add_column("Last Updated")
        table.add_column("Chain of Thought")

        for item in self.action_items:
            table.add_row(
                "✅" if item.is_completed else "❌",
                item.title,
                str(item.last_updated),
                item.chain_of_thought,
            )
        yield table

    def __str__(self) -> str:
        return self.__repr__()


def yield_action_items(transcript: str, state: ActionItemResponse):
    action_items = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        seed=42,
        response_model=Iterable[ActionItem],
        stream=True,
        messages=[
            {
                "role": "system",
                "content": f"""
                You're a world-class note taker. 
                You are given the current state of the notes and an additional piece of the transcript. 
                Use this to update the action.
                
                If you return an action item with the same ID as something in the set, It will be overwritten.
                Use this to update the complete status or change the title if there's more context. 

                - If they are distinct items, do not repeat the slug.
                - Only repeat a slug if we need to update the title or completion status.
                - If the completion status is not mentioned, it should be assumed to be incomplete.
                - For each task describe the success / completion criteria as well.
                - If something is explicitly mentioned as being done, mark it as done. 

                {state.model_dump_json(indent=2)}
                """,
            },
            {
                "role": "user",
                "content": f"Take the following transcript to return a set of transactions from the transcript\n\n{transcript}",
            },
        ],
    )

    for action_item in action_items:
        state = state.patch(action_item)
        yield state


class Application:
    def __init__(self, state=None):
        self.state = ActionItemResponse(action_items=[]) if state is None else state

    def add_transcript(self, transcript: str):
        for new_state in yield_action_items(transcript, self.state):
            self.state = new_state

    def __rich_console__(self, console: Console, options: dict):
        return self.state.__rich_console__(console, options)


if __name__ == "__main__":
    app = Application(
        state=ActionItemResponse(
            action_items=[
                ActionItem(
                    slug="1",
                    title="Do the thing",
                    chain_of_thought="I should do the thing",
                ),
                ActionItem(
                    slug="2",
                    title="Do the other thing",
                    chain_of_thought="I should do the other thing",
                ),
            ]
        )
    )

    console = Console()
    console.print(app.state)
