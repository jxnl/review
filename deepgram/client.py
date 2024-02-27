# Copyright 2023 Deepgram SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

from notes import Application
from rich.console import Console

console = Console()


class LiveNotes:
    """
    Builds up a transcript, and a buffer. The buffer is used to store the last n sentences, and the transcript is the
    full transcript. On udpate, the buffer is added to the transcript, and the buffer is cleared. until the last n messages
    """

    def __init__(self):
        self.transcript = []
        self.deepgram = DeepgramClient()
        self.app = Application()
        self.console = Console()
        self.last_index = 0
        self.n_lines = 0

    def get_context(self, n=5):
        """
        return the transcripts since the last index
        """
        start = max(0, self.last_index - n)
        return self.transcript[start:]

    def add_transcript(self, transcript: str):
        self.transcript.append((self.n_lines, transcript))
        self.n_lines += 1

    def update(self):
        context = self.get_context()
        context_str = "\n".join([line for _, line in context])
        for state in self.app.add_transcript(transcript=context_str):
            self.console.clear()
            self.console.print(state)
        self.last_index = max([i for i, _ in context])

    def render(self):
        self.console.print(self.app)

    def listen(self):
        try:
            dg_connection = self.deepgram.listen.live.v("1")

            def on_message(_self, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript

                self.console.clear()
                self.console.print(f"Listening...: {sentence}")
                self.render()

                if result.speech_final:
                    if len(sentence) == 0:
                        return
                    self.add_transcript(sentence)

            def on_utterance_end(_self, utterance_end, **kwargs):
                self.update()

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)

            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                # To get UtteranceEnd, the following must be set:
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
            )
            dg_connection.start(options)

            # Open a microphone stream on the default input device
            microphone = Microphone(dg_connection.send)

            # start microphone
            microphone.start()

            # wait until finished
            input("Press Enter to stop recording...\n\n")

            # Wait for the microphone to close
            microphone.finish()

            # Indicate that we've finished
            dg_connection.finish()

        except Exception as e:
            print(f"Could not open socket: {e}")
            return


if __name__ == "__main__":
    app = LiveNotes()
    app.listen()
