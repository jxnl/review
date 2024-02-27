from textwrap import dedent
import instructor

from pydantic import BaseModel, Field
from typing import Iterable, List, Literal, Optional
from openai import OpenAI
from rich.console import Console
from langsmith import traceable
from langsmith.wrappers import wrap_openai


client = instructor.patch(wrap_openai(OpenAI()))


options = [
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
    """
    A note is a short piece of information that is actionable or informative.

    - `slug` is a short compact slug like `call-john` required for patching.
    - `notes_type` is the type of the note, Choose the best one. out of {options}
    - `title` is the short title / topic of the note
    - `notes` is the body of the note, should be short
    """

    index: str = Field(
        ...,
        description="Must be a random 3 digit number, unique to the note unless it's a patch. If it's a patch, it should be the same as the note you're patching.",
    )
    notes_type: Optional[str] = Field(
        ..., description="The type of the note, Choose the best one. out of {options}"
    )
    title: str = Field(..., description="Short title / topic of the note")
    notes: Optional[str] = Field(
        default=None,
        description="the body of the note, should be short",
    )


class NewNotes(BaseModel):
    """
    A new set of notes to be patched to the current notes. The notes must not be empty if you want to update the notes.
    """

    notes: List[Note] = Field(
        default_factory=list,
        title="if has_notes is true, then the list must be generated, The list of notes to be patched should only be empty if you don't want to update the notes.",
    )

    def patch(self, new_notes: "NewNotes"):
        if new_notes.notes is None:
            return self

        cur_notes = {note.index: note for note in self.notes if note.index != ""}

        for note in new_notes.notes:
            if isinstance(note, Note):
                cur_notes[note.index] = note

        return NewNotes(notes=list(cur_notes.values()))

    def __rich_console__(self, console: Console, options: dict):
        from rich.table import Table

        table = Table(
            title="Notes in Real Time",
            show_header=True,
            caption="Start speaking to update the notes.",
            padding=(1, 1),
        )
        table.add_column("Type")
        table.add_column("Title")
        table.add_column("Notes")

        for item in self.notes:
            if item.notes is not None:
                table.add_row(
                    type_to_emoji.get(item.notes_type, "📝"),
                    item.title,
                    item.notes,
                )
        yield table


class Application:
    def __init__(self, state=None):
        self.state = NewNotes(notes=[]) if state is None else state

    def yield_partial_state(self, transcript: str) -> Iterable["Application"]:
        print("Adding transcript to the notes.")
        for new_state in self.yield_partial_notes(transcript):
            yield new_state

    def __repr__(self):
        return self.state.__repr__()

    def __str__(self) -> str:
        return self.state.__str__()

    def __rich_console__(self, console: Console, options: dict):
        return self.state.__rich_console__(console, options)

    def yield_partial_notes(self, transcript: str) -> Iterable[NewNotes]:
        partial_notes_generator = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            temperature=0,
            seed=42,
            response_model=instructor.Partial[NewNotes],
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
                    - Must not contain chit-chat or filler words.
                    - Use the full range of note types when appropriate.
                    - Must return a slug that is 2 words, hyphenated, and all lowercase.
                    - None of these feels are allowed to be empty
                    - Only include the notes that are not already in the notes. unless they need to be updated.
                    """
                    ),
                },
            ],
        )

        for partial_notes in partial_notes_generator:
            self.state = self.state.patch(new_notes=partial_notes)
            yield self.state


if __name__ == "__main__":
    app = Application()
    console = Console()

    for state in app.yield_partial_state(
        "Hey this is jason, i wanted to ask when do we want to meet? My goal is to finish the project by the end of the month."
    ):
        console.clear()
        console.print(app)

    for state in app.yield_partial_state(
        "Hey this is jason, i wanted to ask when do we want to meet? My goal is to finish the project by the end of the month. I'm not sure, what do you think? I think we should meet at 3pm right?"
    ):
        console.clear()
        console.print(state)

    for state in app.yield_partial_state(
        "Tony wants to meet at 3pm, but I think we should meet at 4pm. What do you think? John also needs to bring glue for tomorrow"
    ):
        console.clear()
        console.print(state)
