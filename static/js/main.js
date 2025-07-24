document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const githubInput = form.querySelector('textarea[name="github_usernames"]') || form.querySelector('input[name="github_username"]');
            const jobRoleInput = form.querySelector('input[name="job_role"]');
            
            if (githubInput && !githubInput.value.trim()) {
                e.preventDefault();
                alert('Please enter at least one GitHub username.');
            }
            if (jobRoleInput && !jobRoleInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a job role.');
            }
        });
    });
});