document.addEventListener('DOMContentLoaded',()=>{
  const uploadBtn=document.getElementById('uploadBtn');
  const viewBtn=document.getElementById('viewBtn');
  const fileInput=document.getElementById('fileInput');
  const uploadTop=document.getElementById('uploadTop');
  const uploadNav=document.getElementById('uploadNav');

  function openFilePicker(){ fileInput.click(); }
  uploadBtn.addEventListener('click',openFilePicker);
  uploadTop.addEventListener('click',openFilePicker);
  if(uploadNav) uploadNav.addEventListener('click',openFilePicker);

  fileInput.addEventListener('change',e=>{
    const files = Array.from(e.target.files || []);
    if(files.length) alert(`Selected ${files.length} file(s) to upload.`);
  });

  viewBtn.addEventListener('click',()=>{
    document.getElementById('files').scrollIntoView({behavior:'smooth'});
  });

  // delegated file-actions
  document.addEventListener('click',e=>{
    const btn=e.target.closest('button[data-action]');
    if(!btn) return;
    const action=btn.getAttribute('data-action');
    const card=btn.closest('.file-card');
    const name=card?.querySelector('.name')?.textContent || 'file';
    if(action==='download') alert(`Downloading ${name}`);
    if(action==='delete'){
      if(confirm(`Delete ${name}?`)) card.remove();
    }
    if(action==='open') alert(`Open folder ${name}`);
  });
});
