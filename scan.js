const JSON_URL = "songs_fixed.json"; 
const PAUSE = "⏸";
const PLAY = "▶";
const REPEAT = "↺";
let songsData = [];
let html5QrcodeScanner = null;
let player = null;
let currentSong = null;
let currentStartTime = 0; 
let stopTimer = null; 

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

fetch(JSON_URL)
    .then(response => response.json())
    .then(data => {
        songsData = data;
        console.log(`Loaded ${songsData.length} songs.`);
    })
    .catch(err => alert("Error loading songs_fixed.json: " + err));

function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: '300',
        width: '300',
        playerVars: {
            'playsinline': 1,
            'controls': 0,
            'disablekb': 1,
            'origin': window.location.origin 
        },
        events: {
            'onReady': onPlayerReady,
            'onError': onPlayerError 
        }
    });
}

function onPlayerReady(event) { console.log("Player Ready"); }

function onPlayerError(event) {
    let errorMsg = "Error playing video.";
    if (event.data === 100) errorMsg = "Video not found.";
    else if (event.data === 101 || event.data === 150) errorMsg = "Owner disabled embedding.";
    
    alert(errorMsg + "\nTry scanning a different card.");
    resetGame();
}

function warmUpPlayer() {
    if(player && player.playVideo) {
        player.mute();
        player.playVideo();
        setTimeout(() => {
            player.pauseVideo();
            player.unMute(); 
        }, 100);
    }
}

function startScanner() {
    resetGame(); 
    warmUpPlayer();

    document.getElementById("main-controls").style.display = "none";
    document.getElementById("message-area").style.display = "none"; 
    document.getElementById("btn-install").style.display = "none";  
    document.getElementById("scan-container").style.display = "block";
    
    html5QrcodeScanner = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
    
    html5QrcodeScanner.start({ facingMode: "environment" }, config, onScanSuccess)
    .catch(err => {
        alert("Camera Error: " + err);
        resetGame();
    });
}

function onScanSuccess(decodedText, decodedResult) {
    html5QrcodeScanner.stop().then(() => {
        document.getElementById("scan-container").style.display = "none";
        document.getElementById("message-area").style.display = "block";
        document.getElementById("main-controls").style.display = "flex";
        
        let songId = decodedText;
        if (decodedText.includes('Id=')) songId = decodedText.split('Id=')[1];
        songId = parseInt(songId);

        currentSong = songsData.find(s => s.id === songId);
        
        if (currentSong) {
            prepareToPlay();
        } else {
            alert("Song ID not found!");
            resetGame();
        }
    }).catch(err => console.error(err));
}

function prepareToPlay() {
    document.getElementById("message-area").innerText = "Scanned!"; 
    
    document.getElementById("btn-scan").style.display = "none";
    document.getElementById("btn-play-song").style.display = "block";
    
    if(player && player.loadVideoById) {
        player.loadVideoById(currentSong.vidId);
        
        setTimeout(() => {
            calculateRandomStart();
            player.pauseVideo(); 
        }, 800);
    }
}

function calculateRandomStart() {
    currentStartTime = 0;
    if (player && player.getDuration) {
        const duration = player.getDuration();
        if (duration > 110) { 
            const minStart = 50;
            const maxStart = duration - 60;
            currentStartTime = Math.floor(Math.random() * (maxStart - minStart + 1) + minStart);
        } else {
            currentStartTime = 0; 
        }
    }
}

function playAudio() {
    // UI Updates
    document.getElementById("btn-play-song").style.display = "none";
    document.getElementById("active-game-controls").style.display = "flex";
    document.getElementById("btn-reveal").style.display = "block";
    document.getElementById("btn-pause").innerText = PAUSE;
    document.getElementById("message-area").innerText = "🎶 Playing...";
    
    if (navigator.vibrate) navigator.vibrate(200);

    // Audio Playback
    if (player && player.seekTo) {
        player.unMute();
        player.seekTo(currentStartTime);
        player.playVideo();
    }

    startStopTimer();
}

function togglePause() {
    if (player) {
        let state = player.getPlayerState();
        if (state === 1) {
            player.pauseVideo();
            document.getElementById("btn-pause").innerText = PLAY;
            clearTimeout(stopTimer);
        } else {
            player.playVideo();
            document.getElementById("btn-pause").innerText = PAUSE;
            startStopTimer();
        }
    }
}

function replaySong() {
    document.getElementById("message-area").innerText = "Replaying";
    document.getElementById("btn-pause").innerText = PAUSE;
    
    player.seekTo(currentStartTime);
    player.playVideo();

    startStopTimer();
}

function startStopTimer() {
    clearTimeout(stopTimer);
    stopTimer = setTimeout(() => {
        if(player && player.stopVideo) player.stopVideo();
        
        document.getElementById("btn-pause").innerText = PLAY;
        
        if(document.getElementById("song-info").style.display === "none") {
            document.getElementById("message-area").innerText = ""; 
        }
    }, 30000); 
}

function showSongInfo() {
    document.getElementById("message-area").innerText = "Answer";

    let parts = currentSong.date.split('.');
    let monthNum = parseInt(parts[0]);
    let monthAbbr = (monthNum >= 1 && monthNum <= 12) ? MONTHS[monthNum] : "??";
    let year = parts[1] || "????";

    document.getElementById("disp-artist").innerText = currentSong.artist;
    document.getElementById("disp-month").innerText = monthAbbr;
    document.getElementById("disp-year").innerText = year;
    document.getElementById("disp-song").innerText = currentSong.song;

    document.getElementById("song-info").style.display = "block";
    document.getElementById("btn-reveal").style.display = "none";
    
    const installBtn = document.getElementById("btn-install");
    if(installBtn.dataset.canInstall === "true") {
        installBtn.style.display = "inline-block";
    }
}

function resetGame() {
    if (player && player.stopVideo) player.stopVideo();
    clearTimeout(stopTimer);

    currentSong = null;
    
    document.getElementById("scan-container").style.display = "none";
    document.getElementById("song-info").style.display = "none";
    document.getElementById("active-game-controls").style.display = "none";
    document.getElementById("btn-play-song").style.display = "none";
    
    document.getElementById("main-controls").style.display = "flex";
    document.getElementById("btn-scan").style.display = "block";
    
    const msgArea = document.getElementById("message-area");
    msgArea.style.display = "block";
    msgArea.innerText = "Ready to Play";

    const installBtn = document.getElementById("btn-install");
    if(installBtn.dataset.canInstall === "true") {
        installBtn.style.display = "inline-block";
    }
}