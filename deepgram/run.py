# Copyright 2023 Deepgram SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

from tasks import Application
from rich.console import Console

console = Console()

transcript_console = Console()


def merge_strings_with_overlap(sentences):
    if not sentences:
        return ""

    def find_overlap(a, b):
        """
        Find the maximum length of the overlapping part between the end of string a and the start of string b.
        """
        max_overlap_len = min(len(a), len(b))
        for i in range(max_overlap_len, 0, -1):
            if a.endswith(b[:i]):
                return i
        return 0

    merged = sentences[0]  # Start with the first sentence
    for next_sentence in sentences[1:]:
        overlap_len = find_overlap(merged, next_sentence)
        merged += " "  # Add a space between sentences
        merged += next_sentence[overlap_len:]  # Append non-overlapping part
    return merged


def main():
    try:
        deepgram: DeepgramClient = DeepgramClient()

        dg_connection = deepgram.listen.live.v("1")

        global buffer
        buffer = []

        global app
        app = Application()

        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            buffer.append(sentence)

            console.clear()
            global app
            sentence = merge_strings_with_overlap(buffer[-1:-40:-1][::-1])
            console.print(app)
            console.print(f"Buffer: {sentence}")

        def on_metadata(self, metadata, **kwargs):
            # print(f"\n\n{metadata}\n\n")
            pass

        def on_speech_started(self, speech_started, **kwargs):
            pass

        def on_utterance_end(self, utterance_end, **kwargs):
            global app

            buffer_str = merge_strings_with_overlap(
                buffer[-1:-5:-1][::-1]
            )  # get the last 10 sentences
            app.add_transcript(transcript=buffer_str)

        def on_error(self, error, **kwargs):
            # print(f"\n\n{error}\n\n")
            pass

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)

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

        print("Finished")
        # sleep(30)  # wait 30 seconds to see if there is any additional socket activity
        # print("Really done!")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return


if __name__ == "__main__":
    with console.status("Listening..."):
        main()
