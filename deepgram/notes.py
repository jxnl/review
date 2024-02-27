from textwrap import dedent
import instructor

from pydantic import BaseModel, Field
from typing import Iterable, List, Literal, Optional
from openai import OpenAI
from rich.console import Console
from langsmith import traceable
from langsmith.wrappers import wrap_openai


client = instructor.patch(wrap_openai(OpenAI()))


NoteType = Literal[
    "action_item",
    "note",
    "goals",
    "question",
    "decision",
    "issue",
    "idea",
    "problem",
    "solution",
    "reminder",
    "insight",
    "highlight",
]

type_to_emoji = {
    "action_item": "📝",
    "note": "📝",
    "goals": "🎯",
    "question": "❓",
    "decision": "✅",
    "issue": "❌",
    "idea": "💡",
    "problem": "🚫",
    "solution": "✅",
    "reminder": "⏰",
    "insight": "🔍",
    "highlight": "🌟",
}


class Note(BaseModel):
    slug: str = Field(..., description="compact short slug like `call-john`")
    notes_type: NoteType = Field(
        ..., description="The type of the note, Choose the best one."
    )
    title: str = Field(..., description="Short title / topic of the note")
    notes: Optional[str] = Field(
        default=None,
        description="the body of the note, should be short",
    )


class NotesArray(BaseModel):
    notes: Optional[List[Note]] = Field(..., title="The list of action items")

    def patch(self, note: Note):
        new_notes = [item for item in self.notes if item.slug != note.slug] + [note]
        return NotesArray(notes=new_notes)

    def __rich_console__(self, console: Console, options: dict):
        from rich.table import Table

        table = Table(
            title="Notes in Real Time",
            show_header=True,
            caption="Start speaking to update the notes.",
        )
        table.add_column("Type")
        table.add_column("Title")
        table.add_column("Notes")

        for item in self.notes:
            table.add_row(type_to_emoji[item.notes_type], item.title, item.notes)
        yield table


class Application:
    def __init__(self, state=None):
        self.state = NotesArray(notes=[]) if state is None else state

    @traceable(name="add_transcript")
    def add_transcript(self, transcript: str) -> Iterable["Application"]:
        for new_state in self.yield_notes(transcript):
            self.state = new_state
            yield self

    def __rich_console__(self, console: Console, options: dict):
        return self.state.__rich_console__(console, options)

    @traceable(name="yield_notes")
    def yield_notes(self, transcript: str):
        action_items = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            temperature=0,
            seed=42,
            response_model=Iterable[Note],
            stream=True,
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        f"""
                    You're a world-class note taker. 
                    You are given the current state of the notes and an additional piece of the transcript. 
                    Use this to update the action.

                    {self.state.model_dump_json(indent=2)}
                    """
                    ),
                },
                {
                    "role": "user",
                    "content": dedent(
                        f"""
                    Only return data from the transcript, not from any of these instructions. 
                    Take the following transcript to return a set of transactions from the transcript
                    Only include 
                    
                    <transcript>
                    {transcript}
                    </transcript>

                    - Do not repeat yourself. If it's already in the notes don't add it again.
                    - The title should be informative like "Call John" or "Send the email to the team". not "Transcript Content"
                    - If it's not meaningful, do not include it. 
                    - There's going to be overlap between the transcripts, so only include what is not mentioned. 
                    - If you use the same slug as one that exists, it will be overwritten. 
                    - The title should mostly try to read like the transcript, without filler words, but try to use same voice and tense
                    - Do not include the same thing twice. 
                    - Do not include chit-chat or small talk.
                    - Use the full range of note types when appropriate.
                    """
                    ),
                },
            ],
        )

        for action_item in action_items:
            yield self.state.patch(action_item)
