-- Paths injected by setup.sh at compile time
property spotdlPath : "__SPOTDL_PATH__"
property ytdlpPath : "__YTDLP_PATH__"

on run
	try
		set dialogURL to display dialog "Paste a Spotify or YouTube playlist URL:" ¬
			default answer "" ¬
			buttons {"Cancel", "Download"} ¬
			default button "Download" ¬
			cancel button "Cancel" ¬
			with title "Music Downloader"

		set inputURL to text returned of dialogURL

		if inputURL is "" then
			display alert "Error" message "URL cannot be empty." buttons {"OK"} as warning
			return
		end if

		-- Detect source
		set isSpotify to (inputURL contains "spotify.com")
		set isYouTube to (inputURL contains "youtube.com" or inputURL contains "youtu.be")

		if not isSpotify and not isYouTube then
			display alert "Unsupported URL" ¬
				message "Please enter a Spotify or YouTube playlist URL." ¬
				buttons {"OK"} as warning
			return
		end if

		if isSpotify then
			my handleSpotify(inputURL)
		else
			my handleYouTube(inputURL)
		end if

	on error errorMsg number errorNum
		if errorNum is not -128 then
			display alert "An error occurred" message errorMsg buttons {"OK"} as critical
		end if
	end try
end run


on handleSpotify(playlistURL)
	set homeDir to POSIX path of (path to home folder)
	set configPath to homeDir & ".spotdl/config.json"

	-- Check if Spotify credentials are configured
	set hasCredentials to false
	try
		set checkCmd to "python3 -c \"import json,sys; d=json.load(open('" & configPath & "')); v=d.get('client_id',''); sys.exit(0 if v and len(v)>5 else 1)\" 2>/dev/null && echo YES || echo NO"
		set credCheck to do shell script checkCmd
		if credCheck is "YES" then
			set hasCredentials to true
		end if
	end try

	if not hasCredentials then
		-- First-time Spotify setup
		set setupIntro to display alert "Spotify Setup Required" ¬
			message "To download from Spotify, you need a free Spotify Developer account." & return & return & ¬
			"Click 'Open Dashboard' to create an app and get your API credentials." ¬
			buttons {"Cancel", "Open Dashboard"} ¬
			default button "Open Dashboard" ¬
			cancel button "Cancel"

		open location "https://developer.spotify.com/dashboard"

		display alert "Create a Spotify App" ¬
			message "In the dashboard:" & return & ¬
			"1. Click 'Create app'" & return & ¬
			"2. Fill in any name and description" & return & ¬
			"3. Add both Redirect URIs:" & return & ¬
			"   • http://127.0.0.1:9900/" & return & ¬
			"   • http://127.0.0.1:9900" & return & ¬
			"4. Check 'Web API'" & return & ¬
			"5. Go to Settings → copy Client ID and Client Secret" & return & return & ¬
			"Then click OK and enter your credentials." ¬
			buttons {"OK"} default button "OK"

		set idDialog to display dialog "Enter your Spotify Client ID:" ¬
			default answer "" ¬
			buttons {"Cancel", "Next"} ¬
			default button "Next" ¬
			cancel button "Cancel" ¬
			with title "Spotify Setup — Step 1/2"
		set clientId to text returned of idDialog

		set secretDialog to display dialog "Enter your Spotify Client Secret:" ¬
			default answer "" ¬
			buttons {"Cancel", "Save & Download"} ¬
			default button "Save & Download" ¬
			cancel button "Cancel" ¬
			with title "Spotify Setup — Step 2/2"
		set clientSecret to text returned of secretDialog

		-- Save credentials via spotdl
		do shell script "mkdir -p " & quoted form of (homeDir & ".spotdl")
		do shell script spotdlPath & " --client-id " & quoted form of clientId & " --client-secret " & quoted form of clientSecret & " save 2>&1 || true"
	end if

	-- Build output path: ~/Music/music-downloader/<playlist-name>/<pos> - <artists> - <title>.mp3
	set musicDir to POSIX path of (path to music folder)
	set outputTemplate to musicDir & "music-downloader/{list-name}/{list-position} - {artists} - {title}.{output-ext}"

	set cmd to "source ~/.zshrc 2>/dev/null; source ~/.zprofile 2>/dev/null; " & ¬
		spotdlPath & " --config --user-auth download " & quoted form of playlistURL & ¬
		" --bitrate 320k --format mp3 --threads 4" & ¬
		" --output " & quoted form of outputTemplate & ¬
		"; echo ''; echo '✅ Download complete. You can close this window.'"

	tell application "Terminal"
		activate
		do script cmd
	end tell
end handleSpotify


on handleYouTube(videoURL)
	set musicDir to POSIX path of (path to music folder)

	-- Detect playlist vs single video
	set isPlaylist to (videoURL contains "list=")

	if isPlaylist then
		-- %(playlist_title)s resolved automatically by yt-dlp
		set outputTemplate to musicDir & "music-downloader/%(playlist_title)s/%(title)s.%(ext)s"
	else
		-- Single video → ~/Music/music-downloader/YouTube/<uploader> - <title>.mp3
		set outputTemplate to musicDir & "music-downloader/YouTube/%(uploader)s - %(title)s.%(ext)s"
	end if

	set cmd to "source ~/.zshrc 2>/dev/null; source ~/.zprofile 2>/dev/null; " & ¬
		ytdlpPath & " --extract-audio --audio-format mp3" & ¬
		" --postprocessor-args \"ffmpeg:-b:a 320k\"" & ¬
		" --yes-playlist --add-metadata" & ¬
		" --cookies-from-browser safari" & ¬
		" -o " & quoted form of outputTemplate & ¬
		" " & quoted form of videoURL & ¬
		"; echo ''; echo '✅ Download complete. You can close this window.'"

	tell application "Terminal"
		activate
		do script cmd
	end tell
end handleYouTube
