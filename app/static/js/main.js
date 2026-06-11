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

    // Unlock Settings Selector Logic
    const unlockSettingsSection = document.getElementById('unlockSettingsSection');
    const geofenceConfig = document.getElementById('geofenceConfig');
    const randomConfig = document.getElementById('randomConfig');
    const randomPreset = document.getElementById('randomPreset');
    const randomCustomInputs = document.getElementById('randomCustomInputs');
    const getCurrentLocationBtn = document.getElementById('getCurrentLocationBtn');
    
    let selectedUnlockType = 'none';

    if (unlockSettingsSection) {
        const selectButtons = document.querySelectorAll('.unlock-type-selector .btn-select');
        selectButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                selectButtons.forEach(b => {
                    b.classList.remove('active');
                    b.style.border = '1px solid var(--glass-border)';
                    b.style.background = 'rgba(0,0,0,0.25)';
                    b.style.color = 'var(--text-muted)';
                });

                btn.classList.add('active');
                btn.style.border = '1px solid rgba(59, 130, 246, 0.4)';
                btn.style.background = 'rgba(59, 130, 246, 0.1)';
                btn.style.color = 'var(--primary)';

                selectedUnlockType = btn.getAttribute('data-type');
                
                geofenceConfig.style.display = selectedUnlockType === 'geofence' ? 'block' : 'none';
                randomConfig.style.display = selectedUnlockType === 'random' ? 'block' : 'none';
                
                if (typeof feather !== 'undefined') feather.replace();
            });
        });

        // GPS getCurrentPosition
        getCurrentLocationBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert('您的瀏覽器不支援 GPS 定位功能。');
                return;
            }
            getCurrentLocationBtn.disabled = true;
            const originalHTML = getCurrentLocationBtn.innerHTML;
            getCurrentLocationBtn.innerHTML = '定位中...';

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    document.getElementById('targetLatitude').value = position.coords.latitude.toFixed(6);
                    document.getElementById('targetLongitude').value = position.coords.longitude.toFixed(6);
                    getCurrentLocationBtn.disabled = false;
                    getCurrentLocationBtn.innerHTML = originalHTML;
                    if (typeof feather !== 'undefined') feather.replace();
                },
                (err) => {
                    console.error(err);
                    alert('無法取得定位，請確認是否允許瀏覽器存取位置資訊。');
                    getCurrentLocationBtn.disabled = false;
                    getCurrentLocationBtn.innerHTML = originalHTML;
                    if (typeof feather !== 'undefined') feather.replace();
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });

        // Random Preset change helper
        randomPreset.addEventListener('change', () => {
            if (randomPreset.value === 'custom') {
                randomCustomInputs.style.display = 'flex';
            } else {
                randomCustomInputs.style.display = 'none';
            }
        });
    }

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
                    if (unlockSettingsSection) unlockSettingsSection.style.display = 'block';
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
            if (unlockSettingsSection) unlockSettingsSection.style.display = 'block';
            
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

        // Append unlock configurations
        formData.append('unlock_type', selectedUnlockType);
        if (selectedUnlockType === 'geofence') {
            formData.append('location_name', document.getElementById('locationName').value);
            formData.append('latitude', document.getElementById('targetLatitude').value);
            formData.append('longitude', document.getElementById('targetLongitude').value);
            formData.append('radius', document.getElementById('targetRadius').value);
        } else if (selectedUnlockType === 'random') {
            const presetVal = randomPreset.value;
            let minH = 1;
            let maxH = 24;
            if (presetVal === '1-2') {
                minH = 1; maxH = 2;
            } else if (presetVal === '12-24') {
                minH = 12; maxH = 24;
            } else if (presetVal === '24-72') {
                minH = 24; maxH = 72;
            } else if (presetVal === 'custom') {
                minH = parseInt(document.getElementById('randomMinHours').value) || 1;
                maxH = parseInt(document.getElementById('randomMaxHours').value) || 2;
            }
            formData.append('random_min_hours', minH);
            formData.append('random_max_hours', maxH);
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
