from client import LiveNotes

transcripts = [
    "Hey this is jason, when do we want to meet?",
    "I'm not sure, what do you think?",
    "I think we should meet at 3pm",
    "Sounds good to me. I'll see you then.",
    "did we decide on a location?",
    "I think we should meet at the office.",
]

notes = LiveNotes()

notes.add_transcript(transcripts[0])
notes.add_transcript(transcripts[1])

print(notes.get_context())

notes.update()

notes.add_transcript(transcripts[2])
notes.add_transcript(transcripts[3])
notes.add_transcript(transcripts[4])
print(notes.get_context())
notes.update()

notes.add_transcript(transcripts[5])
print(notes.get_context())
notes.update()
