# YouTube Channel & Playlist Agent

Using a Hyperbrowser agent to fetch videos semantically from channels and playlists. To fit in with the text centric paradigm of AI agents,
I used gnurecutils instead of a traditional database. The tasks.rec file contains the list of channels and/or playlists to fetch from, a prompt to use, and the last time the process ran. The Hyperbrowser agent executes the prompts and returns structured JSON that is parsed and sent to me by email using Resend.

The app is deployed on Render and runs every 3 hours.
