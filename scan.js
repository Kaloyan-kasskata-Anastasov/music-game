const JSON_URL = "songs_fixed.json";
let songsData = [];
let html5QrcodeScanner = null;
let player = null;
let currentSong = null;
let currentStartTime = 0;
let waitingForFlip = false;
let stopTimer = null;

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

fetch(JSON_URL)
    .then(response => response.json())
    .then(data => {
        songsData = data;
        console.log(`Loaded ${songsData.length} songs.`);
    })
    .catch(err => alert(`Error loading ${JSON_URL}: ` + err));

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
    if (event.data === 100) errorMsg = "Video not found (deleted/private).";
    else if (event.data === 101 || event.data === 150) errorMsg = "Owner disabled embedding.";

    alert(errorMsg + "\nTry scanning a different card.");
    resetGame();
}

function startScanner() {
    resetGame();

    document.getElementById("btn-scan").style.display = "none";
    document.getElementById("scan-container").style.display = "block";
    document.getElementById("message-area").innerText = "Scan a QR Code";

    // Permission for iOS Orientation
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(response => {
                if (response == 'granted') window.addEventListener('deviceorientation', handleOrientation);
            })
            .catch(console.error);
    } else {
        window.addEventListener('deviceorientation', handleOrientation);
    }

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

        let songId = decodedText;
        if (decodedText.includes('Id=')) songId = decodedText.split('Id=')[1];
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

function prepareForFlip() {
    waitingForFlip = true;
    document.getElementById("message-area").innerText = ""; // Clear text to focus on guide
    document.getElementById("flip-container").style.display = "block";

    // Warm up player
    if (player && player.loadVideoById) {
        player.loadVideoById(currentSong.vidId);
        player.mute();

        setTimeout(() => {
            calculateRandomStart();
            player.pauseVideo();
            player.unMute();
        }, 1000);
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

function handleOrientation(event) {
    if (!waitingForFlip) return;
    const beta = event.beta;
    if (beta > 135 || beta < -135) {
        playAudio();
    }
}

function playAudio() {
    if (!waitingForFlip) return;
    waitingForFlip = false;

    document.getElementById("flip-container").style.display = "none";
    document.getElementById("message-area").innerText = "🎶 Playing...";

    if (navigator.vibrate) navigator.vibrate(200);

    if (player && player.seekTo) {
        player.seekTo(currentStartTime);
        player.playVideo();
    }

    setTimeout(() => {
        showSongInfo();
    }, 1000);

    clearTimeout(stopTimer);
    stopTimer = setTimeout(() => {
        if (player && player.stopVideo) player.stopVideo();
        document.getElementById("message-area").innerText = "Time's Up!";
    }, 30000);
}

function showSongInfo() {
    let parts = currentSong.date.split('.');
    let monthNum = parseInt(parts[0]);
    let monthAbbr = (monthNum >= 1 && monthNum <= 12) ? MONTHS[monthNum] : "??";
    let year = parts[1] || "????";

    document.getElementById("disp-artist").innerText = currentSong.artist;
    document.getElementById("disp-month").innerText = monthAbbr;
    document.getElementById("disp-year").innerText = year;
    document.getElementById("disp-song").innerText = currentSong.song;

    document.getElementById("song-info").style.display = "block";
    document.getElementById("btn-scan").style.display = "inline-block";
    document.getElementById("result-controls").style.display = "block";
}

function replaySong() {
    document.getElementById("message-area").innerText = "Replaying...";
    clearTimeout(stopTimer);

    player.seekTo(currentStartTime);
    player.playVideo();

    stopTimer = setTimeout(() => {
        player.stopVideo();
        document.getElementById("message-area").innerText = "Time's Up!";
    }, 30000);
}

function resetGame() {
    if (player && player.stopVideo) player.stopVideo();
    clearTimeout(stopTimer);

    currentSong = null;
    waitingForFlip = false;

    document.getElementById("scan-container").style.display = "none";
    document.getElementById("song-info").style.display = "none";
    document.getElementById("result-controls").style.display = "none";
    document.getElementById("flip-container").style.display = "none";

    document.getElementById("btn-scan").style.display = "inline-block";
    document.getElementById("message-area").innerText = "Ready to Play";
}