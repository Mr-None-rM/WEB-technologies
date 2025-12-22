document.addEventListener('DOMContentLoaded', function() {
    console.log('Avatar preview script loaded');
    const avatarInput = document.querySelector('.avatar-input');
    if (avatarInput) {
        console.log('Avatar input found');
        avatarInput.addEventListener('change', function(e) {
            console.log('File selected:', e.target.files[0]);
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector('.avatar-preview-image');
                    if (preview) {
                        preview.src = e.target.result;
                        console.log('Preview updated');
                    } else {
                        console.warn('Preview image not found with selector .avatar-preview-image');
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    } else {
        console.log('Avatar input not found with selector .avatar-input');
    }
});