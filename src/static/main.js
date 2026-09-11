const recorder = document.getElementById('recorder');
const player = document.getElementById('player');

recorder.addEventListener('change', function (e) {
  const file = e.target.files[0];
  if (!file) return;
  const url = URL.createObjectURL(file);
  player.src = url;
});

const timestampsCheckbox = document.getElementById('timestamps');
const fileTypeSelect = document.getElementById('file_type');
const TXT_PLACEHOLDER_ID = 'file_type_txt_placeholder';

function syncFileTypeState() {
  const timestampsEnabled = timestampsCheckbox.checked;

  if (!timestampsEnabled) {
    fileTypeSelect.dataset.previousValue = fileTypeSelect.value;

    let placeholder = document.getElementById(TXT_PLACEHOLDER_ID);
    if (!placeholder) {
      placeholder = document.createElement('option');
      placeholder.id = TXT_PLACEHOLDER_ID;
      placeholder.value = 'txt';
      placeholder.textContent = 'txt';
      fileTypeSelect.appendChild(placeholder);
    }
    fileTypeSelect.value = 'txt';
  } else {
    const placeholder = document.getElementById(TXT_PLACEHOLDER_ID);
    if (placeholder) {
      placeholder.remove();
    }
    fileTypeSelect.value = fileTypeSelect.dataset.previousValue || 'srt';
  }

  fileTypeSelect.disabled = !timestampsEnabled;
}

timestampsCheckbox.addEventListener('change', syncFileTypeState);
syncFileTypeState();

const conversionForm = document.getElementById('conversion-form');
const submitButton = document.getElementById('submit');
const spinner = document.getElementById('spinner');

conversionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    submitButton.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const formData = new FormData(conversionForm);
        const response = await fetch('/download/', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Server returned ${response.status}`);
        }

        const cd = response.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename="?([^";]+)"?/);
        const fallbackExt = timestampsCheckbox.checked ? (formData.get('file_type') || 'srt') : 'txt';
        const name = match ? match[1] : `subtitles.${fallbackExt}`;

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = name;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
  } catch (err) {
        console.error(err);
        alert('Conversion failed: ' + err.message);
  } finally {
        submitButton.disabled = false;
        spinner.classList.add('d-none');
  }
});
