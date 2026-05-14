document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('recordBtn');
    const recordText = document.getElementById('recordText');
    const recordingTimer = document.getElementById('recordingTimer');
    const audioUpload = document.getElementById('audioUpload');
    const fileNameDisplay = document.getElementById('fileName');
    const actionSection = document.getElementById('actionSection');
    const submitAudioBtn = document.getElementById('submitAudioBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Only init if on index page
    if (!recordBtn) return;

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let timerInterval;
    let startTime;
    let finalAudioBlob = null;
    let uploadFile = null;

    // Timer logic
    function updateTimer() {
        const diff = Date.now() - startTime;
        const totalSeconds = Math.floor(diff / 1000);
        const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
        const seconds = String(totalSeconds % 60).padStart(2, '0');
        recordingTimer.textContent = `${minutes}:${seconds}`;
    }

    // Audio Recording
    recordBtn.addEventListener('click', async () => {
        if (!isRecording) {
            // Start recording
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };

                mediaRecorder.onstop = () => {
                    finalAudioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    // Ready to submit
                    actionSection.style.display = 'block';
                    uploadFile = null; // Clear upload if recorded
                    fileNameDisplay.textContent = '已錄製音訊';
                };

                mediaRecorder.start();
                isRecording = true;
                
                // UI Updates
                recordBtn.classList.add('recording');
                recordText.textContent = '停止錄音';
                startTime = Date.now();
                timerInterval = setInterval(updateTimer, 1000);
                
                // Reset upload
                audioUpload.value = '';
                
            } catch (err) {
                console.error('Error accessing microphone:', err);
                alert('無法存取麥克風，請確認權限是否開啟。');
            }
        } else {
            // Stop recording
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            
            // UI Updates
            recordBtn.classList.remove('recording');
            recordText.textContent = '重新錄製';
            clearInterval(timerInterval);
        }
    });

    // Audio Upload
    audioUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadFile = file;
            finalAudioBlob = null; // Clear record if uploaded
            fileNameDisplay.textContent = `已選擇：${file.name}`;
            actionSection.style.display = 'block';
            
            // Reset recording UI
            if(isRecording) {
                recordBtn.click(); // Stop if recording
            }
            recordText.textContent = '開始錄音';
            recordingTimer.textContent = '00:00';
        }
    });

    // Submit Audio
    submitAudioBtn.addEventListener('click', async () => {
        if (!finalAudioBlob && !uploadFile) return;

        const formData = new FormData();
        if (finalAudioBlob) {
            formData.append('audio', finalAudioBlob, 'record.webm');
        } else {
            formData.append('audio', uploadFile);
        }

        loadingOverlay.style.display = 'flex';
        submitAudioBtn.disabled = true;

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (data.success) {
                // Redirect to result page
                window.location.href = `/result/${data.record_id}`;
            } else {
                alert(data.error || '上傳失敗');
                loadingOverlay.style.display = 'none';
                submitAudioBtn.disabled = false;
            }
        } catch (err) {
            console.error(err);
            alert('發生錯誤');
            loadingOverlay.style.display = 'none';
            submitAudioBtn.disabled = false;
        }
    });
});
