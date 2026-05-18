const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api/v1'
    : 'https://cloud-storage-backend-web.onrender.com/api/v1';
const STORAGE_KEY = 'cloudvault_session';
const CHUNK_SIZE = 8 * 1024 * 1024;

let currentToken = null;
let currentRefreshToken = null;
let currentUser = null;
let activeFiles = [];

document.addEventListener('DOMContentLoaded', () => {
    bindUi();
    restoreSession();
});

function bindUi() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', async (event) => {
        event.preventDefault();
        uploadArea.classList.remove('dragover');
        await queueUploads([...event.dataTransfer.files]);
    });

    fileInput.addEventListener('change', async (event) => {
        await queueUploads([...event.target.files]);
        fileInput.value = '';
    });

    document.getElementById('filesList').addEventListener('click', handleFileActionClick);
}

function toggleAuthForm(mode) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');

    const showLogin = mode !== 'register';
    loginForm.classList.toggle('hidden', !showLogin);
    registerForm.classList.toggle('hidden', showLogin);
    loginTab.classList.toggle('active', showLogin);
    registerTab.classList.toggle('active', !showLogin);
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        showToast('Enter username and password', 'error');
        return;
    }

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    if (!response.ok) {
        showToast(data.detail || 'Login failed', 'error');
        return;
    }

    persistSession({
        token: data.access_token,
        refreshToken: data.refresh_token,
        username
    });
    showToast('Login successful', 'success');
    await enterDashboard();
}

async function handleRegister() {
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;

    if (!username || !email || !password || !passwordConfirm) {
        showToast('Fill all sign-up fields', 'error');
        return;
    }

    if (password !== passwordConfirm) {
        showToast('Passwords do not match', 'error');
        return;
    }

    const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    const data = await response.json();
    if (!response.ok) {
        showToast(data.detail || 'Registration failed', 'error');
        return;
    }

    persistSession({
        token: data.access_token,
        refreshToken: data.refresh_token,
        username
    });
    showToast('Account created', 'success');
    await enterDashboard();
}

async function refreshSession() {
    if (!currentRefreshToken) {
        showToast('No refresh token stored', 'error');
        return;
    }

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: currentRefreshToken })
    });

    const data = await response.json();
    if (!response.ok) {
        handleLogout();
        showToast(data.detail || 'Session expired', 'error');
        return;
    }

    currentToken = data.access_token;
    persistSession({ token: currentToken, refreshToken: currentRefreshToken, username: currentUser });
    showToast('Access token refreshed', 'success');
    setStatus('tokenStatus', 'Refreshed');
}

async function handleLogout() {
    if (currentRefreshToken) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: currentRefreshToken })
        }).catch(() => {});
    }

    clearSession();
    addActivity('Logged out and cleared local session');
    showAuthScreen();
    showToast('Logged out', 'info');
}

function persistSession({ token, refreshToken, username }) {
    currentToken = token;
    currentRefreshToken = refreshToken;
    currentUser = username;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, refreshToken, username }));
}

function clearSession() {
    currentToken = null;
    currentRefreshToken = null;
    currentUser = null;
    activeFiles = [];
    localStorage.removeItem(STORAGE_KEY);
}

function restoreSession() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
        showAuthScreen();
        return;
    }

    try {
        const saved = JSON.parse(raw);
        currentToken = saved.token || null;
        currentRefreshToken = saved.refreshToken || null;
        currentUser = saved.username || null;
    } catch {
        showAuthScreen();
        return;
    }

    if (!currentToken || !currentUser) {
        showAuthScreen();
        return;
    }

    enterDashboard();
}

function showAuthScreen() {
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('dashboardSection').classList.add('hidden');
    toggleAuthForm('login');
    clearInputs();
}

async function enterDashboard() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('dashboardSection').classList.remove('hidden');
    document.getElementById('userDisplay').textContent = `Signed in as ${currentUser}`;
    addActivity('Dashboard opened');

    try {
        const response = await authedFetch(`${API_BASE_URL}/auth/me`);
        if (response.ok) {
            document.getElementById('apiStatus').textContent = 'Online';
        }
    } catch {
        document.getElementById('apiStatus').textContent = 'Unavailable';
    }

    await loadFiles();
    showPanel('overviewPanel');
}

function clearInputs() {
    ['loginUsername', 'loginPassword', 'registerUsername', 'registerEmail', 'registerPassword', 'registerPasswordConfirm']
        .forEach((id) => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });
}

function showPanel(panelId) {
    document.querySelectorAll('.dashboard .panel').forEach((panel) => panel.classList.add('hidden'));
    document.getElementById(panelId).classList.remove('hidden');
    document.getElementById(panelId).classList.add('visible');

    document.querySelectorAll('.nav-chip').forEach((chip) => chip.classList.remove('active'));
    document.querySelector(`.nav-chip[data-panel="${panelId}"]`)?.classList.add('active');
}

function handleFileActionClick(event) {
    const button = event.target.closest('button[data-action]');
    if (!button) return;

    const fileId = Number(button.dataset.id);
    const action = button.dataset.action;
    const fileName = button.dataset.name || 'file';

    if (action === 'download') {
        downloadFile(fileId, fileName);
    }

    if (action === 'delete') {
        deleteFile(fileId, fileName);
    }

    if (action === 'versions') {
        document.getElementById('versionFileSelect').value = String(fileId);
        showPanel('versionsPanel');
        loadVersionHistory();
    }

    if (action === 'copy-url') {
        copyDownloadUrl(fileId, fileName);
    }
}

async function authedFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            Authorization: `Bearer ${currentToken}`
        }
    });

    if (response.status === 401 && currentRefreshToken) {
        await refreshSession();
        return fetch(url, {
            ...options,
            headers: {
                ...(options.headers || {}),
                Authorization: `Bearer ${currentToken}`
            }
        });
    }

    return response;
}

async function queueUploads(files) {
    if (!files.length) return;
    showPanel('uploadPanel');

    for (const file of files) {
        await uploadMultipartFile(file);
    }
}

async function uploadMultipartFile(file) {
    const progressWrap = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('uploadStatus');
    const queueList = document.getElementById('uploadQueue');

    progressWrap.classList.remove('hidden');
    progressText.textContent = `Preparing ${file.name}`;
    queueList.innerHTML = `<div class="activity-item">Uploading ${file.name}</div>`;

    try {
        const initResponse = await authedFetch(`${API_BASE_URL}/files/multipart/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_name: file.name,
                file_size: file.size,
                file_type: file.type || 'application/octet-stream'
            })
        });

        const initData = await initResponse.json();
        if (!initResponse.ok) throw new Error(initData.detail || 'Could not create upload session');

        const totalParts = initData.total_parts;
        const parts = [];

        for (let partNumber = 1; partNumber <= totalParts; partNumber += 1) {
            const presignResponse = await authedFetch(`${API_BASE_URL}/files/multipart/presign-part`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_id: initData.upload_id,
                    s3_key: initData.s3_key,
                    part_number: partNumber
                })
            });

            const presignData = await presignResponse.json();
            if (!presignResponse.ok) throw new Error(presignData.detail || 'Could not presign part');

            const start = (partNumber - 1) * CHUNK_SIZE;
            const chunk = file.slice(start, start + CHUNK_SIZE);

            const uploadResult = await fetch(presignData.url, {
                method: 'PUT',
                body: chunk
            });

            if (!uploadResult.ok) throw new Error(`Chunk ${partNumber} failed`);

            parts.push({
                part_number: partNumber,
                etag: uploadResult.headers.get('etag')?.replaceAll('"', '') || `part-${partNumber}`
            });

            const pct = Math.round((partNumber / totalParts) * 100);
            progressFill.style.width = `${pct}%`;
            progressText.textContent = `Uploading ${file.name}: ${pct}%`;
        }

        const completeResponse = await authedFetch(`${API_BASE_URL}/files/multipart/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                upload_id: initData.upload_id,
                s3_key: initData.s3_key,
                parts
            })
        });

        const completeData = await completeResponse.json();
        if (!completeResponse.ok) throw new Error(completeData.detail || 'Could not complete upload');

        addActivity(`Uploaded ${file.name}`);
        showToast(`${file.name} uploaded successfully`, 'success');
        progressFill.style.width = '0%';
        progressText.textContent = 'Upload complete';
        await loadFiles();
    } catch (error) {
        progressFill.style.width = '0%';
        progressText.textContent = 'Upload failed';
        showToast(error.message || 'Upload failed', 'error');
        addActivity(`Upload failed for ${file.name}`);
    } finally {
        setTimeout(() => progressWrap.classList.add('hidden'), 1200);
    }
}

async function loadFiles() {
    const response = await authedFetch(`${API_BASE_URL}/files`);
    const data = await response.json();

    if (!response.ok) {
        showToast(data.detail || 'Could not load files', 'error');
        return;
    }

    activeFiles = data;
    renderFiles(data);
    renderVersionFileSelect(data);
    document.getElementById('fileCount').textContent = String(data.length);
    addActivity(`Loaded ${data.length} files`);
}

function renderFiles(files) {
    const filesList = document.getElementById('filesList');

    if (!files.length) {
        filesList.innerHTML = '<div class="empty-state">No files yet. Upload your first file.</div>';
        return;
    }

    filesList.innerHTML = '';
    files.forEach((file) => filesList.appendChild(createFileCard(file)));
}

function createFileCard(file) {
    const card = document.createElement('article');
    card.className = 'file-card';

    const uploadedAt = new Date(file.upload_time || Date.now()).toLocaleString();

    card.innerHTML = `
        <div class="file-head">
            <div>
                <div class="file-name" title="${file.file_name}">${file.file_name}</div>
                <div class="file-meta">v${file.latest_version} • ${formatFileSize(file.file_size || 0)} • ${uploadedAt}</div>
            </div>
            <div class="file-meta">${file.status}</div>
        </div>
        <div class="file-actions">
            <button class="secondary-btn" data-action="download" data-id="${file.file_id}" data-name="${file.file_name}">Download</button>
            <button class="secondary-btn" data-action="versions" data-id="${file.file_id}" data-name="${file.file_name}">Versions</button>
            <button class="secondary-btn" data-action="copy-url" data-id="${file.file_id}" data-name="${file.file_name}">Copy URL</button>
            <button class="danger-btn" data-action="delete" data-id="${file.file_id}" data-name="${file.file_name}">Delete</button>
        </div>
    `;

    return card;
}

function renderVersionFileSelect(files) {
    const select = document.getElementById('versionFileSelect');
    select.innerHTML = files.length
        ? files.map((file) => `<option value="${file.file_id}">${file.file_name}</option>`).join('')
        : '<option value="">No files available</option>';
}

async function loadVersionHistory() {
    const fileId = document.getElementById('versionFileSelect').value;
    const versionList = document.getElementById('versionList');

    if (!fileId) {
        versionList.innerHTML = '<div class="empty-state compact">Choose a file first.</div>';
        return;
    }

    const response = await authedFetch(`${API_BASE_URL}/files/${fileId}/versions`);
    const data = await response.json();

    if (!response.ok) {
        showToast(data.detail || 'Could not load versions', 'error');
        return;
    }

    if (!data.length) {
        versionList.innerHTML = '<div class="empty-state compact">No versions recorded yet.</div>';
        return;
    }

    versionList.innerHTML = '';
    data.forEach((version) => {
        const item = document.createElement('article');
        item.className = 'version-card';
        item.innerHTML = `
            <div class="file-head">
                <div>
                    <div class="file-name">Version ${version.version_number}</div>
                    <div class="version-meta">${formatFileSize(version.file_size)} • ${new Date(version.upload_time).toLocaleString()}</div>
                </div>
                <button class="secondary-btn" data-action="restore-version" data-id="${fileId}" data-version="${version.version_number}">Restore</button>
            </div>
            <div class="file-meta">${version.s3_url || 'Stored in S3'}</div>
        `;
        versionList.appendChild(item);
    });

    versionList.querySelectorAll('[data-action="restore-version"]').forEach((button) => {
        button.addEventListener('click', async () => {
            await restoreVersion(Number(button.dataset.id), Number(button.dataset.version));
        });
    });
}

async function restoreVersion(fileId, versionNumber) {
    const response = await authedFetch(`${API_BASE_URL}/files/${fileId}/versions/${versionNumber}/restore`, {
        method: 'POST'
    });

    const data = await response.json();
    if (!response.ok) {
        showToast(data.detail || 'Restore failed', 'error');
        return;
    }

    addActivity(`Restored file ${fileId} to version ${versionNumber}`);
    showToast(`Restored version ${versionNumber}`, 'success');
    await loadFiles();
    await loadVersionHistory();
}

async function copyDownloadUrl(fileId, fileName) {
    const response = await authedFetch(`${API_BASE_URL}/files/${fileId}/download-url`);
    const data = await response.json();

    if (!response.ok) {
        showToast(data.detail || 'Could not create download URL', 'error');
        return;
    }

    await navigator.clipboard.writeText(data.url);
    addActivity(`Copied presigned link for ${fileName}`);
    showToast('Presigned URL copied', 'success');
}

async function downloadFile(fileId, filename) {
    const response = await authedFetch(`${API_BASE_URL}/files/${fileId}/download-url`);
    const data = await response.json();

    if (!response.ok) {
        showToast(data.detail || 'Could not get download URL', 'error');
        return;
    }

    window.open(data.url, '_blank', 'noopener,noreferrer');
    addActivity(`Opened download link for ${filename}`);
    showToast('Download link opened', 'success');
}

async function deleteFile(fileId, filename) {
    if (!confirm(`Delete ${filename}?`)) return;

    const response = await authedFetch(`${API_BASE_URL}/files/${fileId}`, {
        method: 'DELETE'
    });

    const data = await response.json();
    if (!response.ok) {
        showToast(data.detail || 'Delete failed', 'error');
        return;
    }

    addActivity(`Deleted ${filename}`);
    showToast('File deleted', 'success');
    await loadFiles();
}

function addActivity(message) {
    const activityList = document.getElementById('activityList');
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
    activityList.prepend(item);
}

function setStatus(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function copyApiPath(path) {
    navigator.clipboard.writeText(`${API_BASE_URL}${path}`);
    showToast(`Copied ${path}`, 'success');
}

function formatFileSize(bytes) {
    if (!bytes) return '0 Bytes';
    const units = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const index = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round((bytes / 1024 ** index) * 100) / 100} ${units[index]}`;
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 2800);
}
