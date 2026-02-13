const JSON_URL = "songs_fixed.json"; 
let songsData = [];
let html5QrcodeScanner = null;
let player = null;
let currentSong = null;
let currentStartTime = 0; 
let stopTimer = null; 

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Load Data
fetch(JSON_URL)
    .then(response => response.json())
    .then(data => {
        songsData = data;
        console.log(`Loaded ${songsData.length} songs.`);
    })
    .catch(err => alert("Error loading songs_fixed.json: " + err));

// YouTube API
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

    document.getElementById("controls").style.display = "none";
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
    document.getElementById("message-area").innerText = "Card Scanned!"; 
    
    // Show Action Container & Play Button
    document.getElementById("action-container").style.display = "block";
    document.getElementById("btn-play-song").style.display = "inline-block";
    document.getElementById("btn-reveal").style.display = "none";
    
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
        if (duration > 90) {
            const minStart = 30;
            const maxStart = duration - 60;
            currentStartTime = Math.floor(Math.random() * (maxStart - minStart + 1) + minStart);
        }
    }
}

function playAudio() {
    // Hide Play, Show Reveal
    document.getElementById("btn-play-song").style.display = "none";
    document.getElementById("btn-reveal").style.display = "inline-block";
    document.getElementById("message-area").innerText = "🎶 Playing...";
    
    if (navigator.vibrate) navigator.vibrate(200);

    if (player && player.seekTo) {
        player.unMute();
        player.seekTo(currentStartTime);
        player.playVideo();
    }

    clearTimeout(stopTimer);
    stopTimer = setTimeout(() => {
        if(player && player.stopVideo) player.stopVideo();
        
        // Only change text if they haven't revealed it yet
        if(document.getElementById("song-info").style.display === "none") {
            document.getElementById("message-area").innerText = "Time's Up! Click Reveal."; 
        }
    }, 30000); 
}

function showSongInfo() {
    // Hide Action Container completely
    document.getElementById("action-container").style.display = "none";
    document.getElementById("message-area").innerText = "Answer Revealed!";

    let parts = currentSong.date.split('.');
    let monthNum = parseInt(parts[0]);
    let monthAbbr = (monthNum >= 1 && monthNum <= 12) ? MONTHS[monthNum] : "??";
    let year = parts[1] || "????";

    document.getElementById("disp-artist").innerText = currentSong.artist;
    document.getElementById("disp-month").innerText = monthAbbr;
    document.getElementById("disp-year").innerText = year;
    document.getElementById("disp-song").innerText = currentSong.song;

    // Show the data
    document.getElementById("song-info").style.display = "block";
    
    // Show replay & scan next controls
    document.getElementById("controls").style.display = "block";
    document.getElementById("btn-scan").style.display = "inline-block"; 
    document.getElementById("result-controls").style.display = "block"; 
    
    const installBtn = document.getElementById("btn-install");
    if(installBtn.dataset.canInstall === "true") {
        installBtn.style.display = "inline-block";
    }
}

function replaySong() {
    document.getElementById("message-area").innerText = "Replaying...";
    clearTimeout(stopTimer);
    
    player.seekTo(currentStartTime);
    player.playVideo();

    stopTimer = setTimeout(() => {
        player.stopVideo();
        document.getElementById("message-area").innerText = "Answer Revealed!";
    }, 30000);
}

function resetGame() {
    if (player && player.stopVideo) player.stopVideo();
    clearTimeout(stopTimer);

    currentSong = null;
    
    // Hide Game UI
    document.getElementById("scan-container").style.display = "none";
    document.getElementById("song-info").style.display = "none";
    document.getElementById("result-controls").style.display = "none";
    document.getElementById("action-container").style.display = "none";
    
    // Reset to "Ready" state
    document.getElementById("controls").style.display = "block";
    document.getElementById("btn-scan").style.display = "inline-block";
    
    const msgArea = document.getElementById("message-area");
    msgArea.style.display = "block";
    msgArea.innerText = "Ready to Play";

    const installBtn = document.getElementById("btn-install");
    if(installBtn.dataset.canInstall === "true") {
        installBtn.style.display = "inline-block";
    }
}