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
    - `notes_type` is the type of the note,
    - `title` is the short title / topic of the note
    - `notes` is the body of the note, should be short
    """

    index: str = Field(
        ...,
        description="Must be a random 3 digit number, unique to the note unless it's a patch. If it's a patch, it should be the same as the note you're patching.",
    )
    notes_type: Optional[str] = Field(
        ..., description=f"The type of the note, Choose the best one. out of {options}"
    )
    title: str = Field(..., description="Short title / topic of the note")
    notes: Optional[str] = Field(
        default=None,
        description="the body of the note, should be short",
    )


class NewNotes(BaseModel):
    """
    This class facilitates the addition of new notes to an existing collection. To update the collection, ensure the notes are not empty. To replace an existing note, provide a new note with an identical index to the one you wish to overwrite.
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

    def yield_partial_state(self, transcript: str):
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
                    As an expert note taker, strive to compile notes that are clear, actionable, and enriching.  
                    You're presented with the current notes' state alongside a new transcript segment. 

                    {self.state.model_dump_json(indent=2)}

                    Aim to enrich existing notes with additional details instead of creating new ones whenever feasible. 
                    Achieve this by employing a function that utilizes an existing note's index for updates. 

                    Be mindful of the note types at your disposal for proper note classification:

                    {options}
                    """
                    ),
                },
                {
                    "role": "user",
                    "content": dedent(
                        f"""
                    Extract only relevant data from the transcript, excluding any of these instructions. 
                    Utilize the provided transcript to extract actionable notes:
                    
                    <transcript>
                    {transcript}
                    </transcript>

                    - Avoid redundancy. Do not add information that is already captured in the notes.
                    - Titles should be clear and actionable, such as "Call John" or "Email the team", rather than vague like "Transcript Content".
                    - Exclude non-essential information.
                    - Given the potential for overlap in transcripts, ensure only new or unmentioned details are included.
                    - Be cautious with slugs; using an existing slug will result in its content being replaced.
                    - Titles should reflect the essence of the transcript, omitting unnecessary words, while maintaining the original voice and tense.
                    - Refrain from duplicating entries.
                    - Omit trivial conversation and filler words.
                    - Appropriately utilize the available note types.
                    - Slugs should consist of two words, connected by a hyphen, in lowercase.
                    - Ensure no fields are left empty.
                    - Incorporate notes not previously included, or update those that require revision.
                    """
                    ),
                },
            ],
        )  # type: ignore

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
