# smart-karaoke

## Song Database
Preprocessing: Melody string constructed from analysing the track in each MIDI file that is closest to the main melody. The melody string is in single semitone granularity (e.g. equal to the MIDI note granularity) and encodes as a strig written to txt.

Startup: SongDatabase reads the preprocessed melody files and converts them into array-of-steps: an int array where each element equals the semitone steps of the interval of two sequential notes. Ex: [5, 0, 0, -2] etc. The melodies are made available in this format by the exposed methods.

Runtime: Once a song has been identified may want to load the song accompaniment file. OR may want to load at startup if memory allows for faster performance?
