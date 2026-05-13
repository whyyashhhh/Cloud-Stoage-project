/* CloudVault dashboard script - API-backed
   Supports: multipart upload, list, download (presigned), delete, restore
*/

const API_BASE_URL = 'http://localhost:8000/api/v1';
const CHUNK_SIZE = 8 * 1024 * 1024;

let token = localStorage.getItem('token');

function showToast(msg) {
  alert(msg);
}

function formatFileSize(bytes){
  if(!bytes) return '0 Bytes';
  const units=['Bytes','KB','MB','GB'];
  const i=Math.floor(Math.log(bytes)/Math.log(1024));
  return Math.round((bytes/1024**i)*100)/100 + ' ' + units[i];
}

async function ensureAuth(){
  if(!token){
    window.location.href='/modern-login.html';
    return false;
  }
  try{
    const r=await fetch(`${API_BASE_URL}/auth/me`,{headers:{Authorization:`Bearer ${token}`}});
    if(!r.ok) throw new Error('auth');
    return true;
  }catch(e){
    localStorage.removeItem('token');
    window.location.href='/modern-login.html';
    return false;
  }
}

function createGridCard(file){
  const card = document.createElement('div');
  card.className='file-card glass';
  card.innerHTML = `
    <div class="file-meta"><div class="icon">📄</div><div><div class="name">${file.file_name}</div><div class="meta muted">${formatFileSize(file.file_size)} • ${new Date(file.upload_time).toLocaleDateString()}</div></div></div>
    <div class="actions">
      <button data-action="download" data-id="${file.file_id}" data-name="${file.file_name}">⬇️</button>
      <button data-action="restore" data-id="${file.file_id}" data-name="${file.file_name}">⤴️</button>
      <button data-action="delete" data-id="${file.file_id}" class="danger">🗑️</button>
    </div>`;
  return card;
}

function renderFiles(files){
  const filesGrid=document.getElementById('filesGrid');
  filesGrid.innerHTML='';
  if(!files.length){
    filesGrid.innerHTML='<div class="file-card glass"><div class="file-meta">No files yet</div></div>';
    return;
  }
  files.forEach(f=>filesGrid.appendChild(createGridCard(f)));
}

async function loadFiles(){
  const r = await fetch(`${API_BASE_URL}/files`,{headers:{Authorization:`Bearer ${token}`}});
  if(!r.ok){ showToast('Could not load files'); return; }
  const data = await r.json();
  renderFiles(data);
}

async function uploadMultipart(file){
  try{
    const initR = await fetch(`${API_BASE_URL}/files/multipart/init`,{
      method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`},
      body: JSON.stringify({file_name:file.name,file_size:file.size,file_type:file.type||'application/octet-stream'})
    });
    const init = await initR.json(); if(!initR.ok) throw new Error(init.detail||'init failed');

    const parts = [];
    for(let part=1; part<=init.total_parts; part++){
      const presignR = await fetch(`${API_BASE_URL}/files/multipart/presign-part`,{
        method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`},
        body: JSON.stringify({upload_id:init.upload_id,s3_key:init.s3_key,part_number:part})
      });
      const presign = await presignR.json(); if(!presignR.ok) throw new Error(presign.detail||'presign failed');

      const start=(part-1)*CHUNK_SIZE; const chunk = file.slice(start,start+CHUNK_SIZE);
      const upR = await fetch(presign.url,{method:'PUT', body:chunk}); if(!upR.ok) throw new Error('upload part failed');
      const etag = upR.headers.get('etag')?.replaceAll('"','')||`part-${part}`;
      parts.push({part_number:part, etag});
    }

    const compR = await fetch(`${API_BASE_URL}/files/multipart/complete`,{
      method:'POST', headers:{'Content-Type':'application/json', Authorization:`Bearer ${token}`},
      body: JSON.stringify({upload_id:init.upload_id,s3_key:init.s3_key,parts})
    });
    const comp = await compR.json(); if(!compR.ok) throw new Error(comp.detail||'complete failed');
    showToast(`${file.name} uploaded`);
    await loadFiles();
  }catch(e){ showToast(e.message||String(e)); }
}

async function downloadFile(fileId){
  const r = await fetch(`${API_BASE_URL}/files/${fileId}/download-url`,{headers:{Authorization:`Bearer ${token}`}});
  const data = await r.json(); if(!r.ok){ showToast(data.detail||'could not get download'); return; }
  window.open(data.url,'_blank');
}

async function deleteFile(fileId){
  if(!confirm('Delete?')) return;
  const r = await fetch(`${API_BASE_URL}/files/${fileId}`,{method:'DELETE', headers:{Authorization:`Bearer ${token}`}});
  if(!r.ok){ showToast('Delete failed'); return; }
  showToast('Deleted'); await loadFiles();
}

async function restoreFile(fileId){
  try{
    const vR = await fetch(`${API_BASE_URL}/files/${fileId}/versions`,{headers:{Authorization:`Bearer ${token}`}});
    const versions = await vR.json(); if(!vR.ok) throw new Error('could not get versions');
    if(!versions.length){ showToast('No versions'); return; }
    const ver = prompt('Enter version number to restore', String(versions[0].version_number));
    if(!ver) return; const rv = await fetch(`${API_BASE_URL}/files/${fileId}/versions/${ver}/restore`,{method:'POST', headers:{Authorization:`Bearer ${token}`}});
    if(!rv.ok) { const d=await rv.json(); showToast(d.detail||'restore failed'); return; }
    showToast('Restored'); await loadFiles();
  }catch(e){ showToast(e.message||String(e)); }
}

document.addEventListener('DOMContentLoaded', async ()=>{
  if(!(await ensureAuth())) return;
  await loadFiles();

  document.getElementById('gridView').addEventListener('click', ()=>{document.getElementById('filesGrid').classList.remove('hidden'); document.getElementById('filesList').classList.add('hidden');});
  document.getElementById('listView').addEventListener('click', ()=>{document.getElementById('filesGrid').classList.add('hidden'); document.getElementById('filesList').classList.remove('hidden');});

  document.getElementById('navUpload')?.addEventListener('click', ()=>document.getElementById('filePicker').click());

  document.getElementById('filePicker')?.addEventListener('change', async (e)=>{
    const files = Array.from(e.target.files||[]);
    for(const f of files) await uploadMultipart(f);
    e.target.value='';
  });

  document.addEventListener('click', async (e)=>{
    const btn = e.target.closest('button[data-action]'); if(!btn) return;
    const action = btn.getAttribute('data-action'); const id = Number(btn.dataset.id);
    if(action==='download') await downloadFile(id);
    if(action==='delete') await deleteFile(id);
    if(action==='restore') await restoreFile(id);
  });
});
