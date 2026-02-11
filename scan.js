// --- CONFIGURATION ---
const JSON_URL = "songs.json"; 
let songsData = [];
let html5QrcodeScanner = null;
let player = null;
let currentSong = null;
let currentStartTime = 0; // Stores the specific 30s segment start time
let scanActive = false;
let waitingForFlip = false;
let stopTimer = null; // Reference to the 30s timer

// --- 1. LOAD DATA ---
fetch(JSON_URL)
    .then(response => response.json())
    .then(data => {
        songsData = data;
        console.log(`Loaded ${songsData.length} songs.`);
    })
    .catch(err => alert("Error loading songs.json: " + err));

// --- 2. YOUTUBE API SETUP ---
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: '300',
        width: '300',
        playerVars: {
            'playsinline': 1,
            'controls': 0,
            'disablekb': 1
        },
        events: {
            'onReady': onPlayerReady
        }
    });
}

function onPlayerReady(event) {
    console.log("YouTube Player Ready");
}

// --- 3. SCANNER LOGIC ---
function startScanner() {
    // 1. Clean up previous state
    resetGame(); 

    // 2. UI Updates
    document.getElementById("btn-scan").style.display = "none";
    document.getElementById("result-controls").style.display = "none";
    document.getElementById("song-info").style.display = "none";
    document.getElementById("scan-container").style.display = "block";
    document.getElementById("message-area").innerText = "Scan a QR Code";
    
    // 3. Permissions (iOS specific)
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(response => {
                if (response == 'granted') {
                    window.addEventListener('deviceorientation', handleOrientation);
                }
            })
            .catch(console.error);
    } else {
        window.addEventListener('deviceorientation', handleOrientation);
    }

    // 4. Start Camera
    html5QrcodeScanner = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
    
    html5QrcodeScanner.start({ facingMode: "environment" }, config, onScanSuccess)
    .catch(err => {
        alert("Camera Error: " + err);
        resetGame(); // Shows SCAN button again if error
    });
}

function onScanSuccess(decodedText, decodedResult) {
    html5QrcodeScanner.stop().then(() => {
        document.getElementById("scan-container").style.display = "none";
        
        let songId = decodedText.split('Id=')[1] || decodedText;
        songId = parseInt(songId);

        currentSong = songsData.find(s => s.id === songId);
        
        if (currentSong) {
            prepareForFlip();
        } else {
            alert("Song ID not found!");
            resetGame();
        }
    }).catch(err => console.error(err));
}

// --- 4. FLIP DETECTION & PLAYBACK ---
function prepareForFlip() {
    waitingForFlip = true;
    document.getElementById("message-area").innerText = "Flip Phone Face Down to Play!";
    document.getElementById("flip-guide").style.display = "block";
    
    // Calculate the random start time NOW (so replay uses the same spot)
    calculateRandomStart();

    // "Warm up" the player (mute play/pause hack)
    if(player && player.loadVideoById) {
        player.mute();
        player.loadVideoById(currentSong.vidId);
        setTimeout(() => { 
            player.pauseVideo(); 
            player.unMute(); 
        }, 500); 
    }
}

function calculateRandomStart() {
    // Default to 0
    currentStartTime = 0;
    
    if (player && player.getDuration) {
        const duration = player.getDuration();
        if (duration > 90) {
            const minStart = 30;
            const maxStart = duration - 60;
            currentStartTime = Math.floor(Math.random() * (maxStart - minStart + 1) + minStart);
        }
    }
}

function handleOrientation(event) {
    if (!waitingForFlip) return;

    // Detect Face Down (>135 or <-135 degrees)
    const beta = event.beta; 
    if (beta > 135 || beta < -135) {
        // Phone is flipped!
        waitingForFlip = false; 
        playAudio();
    }
}

function playAudio() {
    if (!currentSong || !player) return;

    // 1. UI Feedback
    document.getElementById("message-area").innerText = "Playing...";
    document.getElementById("flip-guide").style.display = "none";
    if (navigator.vibrate) navigator.vibrate(200);

    // 2. Play Video at calculated start time
    player.seekTo(currentStartTime);
    player.playVideo();

    // 3. Show Info after 1 second delay
    setTimeout(() => {
        showSongInfo();
    }, 1000);

    // 4. Set timer to stop after 30 seconds
    clearTimeout(stopTimer);
    stopTimer = setTimeout(() => {
        player.stopVideo();
        document.getElementById("message-area").innerText = "Finished"; 
    }, 30000); 
}

function showSongInfo() {
    // Populate Data
    document.getElementById("disp-artist").innerText = currentSong.artist;
    document.getElementById("disp-song").innerText = currentSong.song;
    document.getElementById("disp-year").innerText = currentSong.date;

    // Reveal Info & Buttons
    document.getElementById("song-info").style.display = "block";
    document.getElementById("btn-scan").style.display = "inline-block"; // Show SCAN button
    document.getElementById("result-controls").style.display = "block"; // Show REPLAY button
}

// --- 5. CONTROLS ---
function replaySong() {
    document.getElementById("message-area").innerText = "Replaying...";
    
    // Stop any existing stop timer
    clearTimeout(stopTimer);
    
    // Play from the SAME start time
    player.seekTo(currentStartTime);
    player.playVideo();

    // Set new 30s stop timer
    stopTimer = setTimeout(() => {
        player.stopVideo();
        document.getElementById("message-area").innerText = "Finished";
    }, 30000);
}

function resetGame() {
    // Stop audio if playing
    if (player && player.stopVideo) {
        player.stopVideo();
    }
    clearTimeout(stopTimer);

    // Reset state
    currentSong = null;
    waitingForFlip = false;
    
    // Reset UI to initial state (Scan button visible, info hidden)
    document.getElementById("scan-container").style.display = "none";
    document.getElementById("song-info").style.display = "none";
    document.getElementById("result-controls").style.display = "none";
    document.getElementById("btn-scan").style.display = "inline-block";
    document.getElementById("message-area").innerText = "Ready to Play";
    document.getElementById("flip-guide").style.display = "none";
}