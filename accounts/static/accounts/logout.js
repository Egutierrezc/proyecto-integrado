document.querySelectorAll('.logout-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
        if (!window.confirm('¿Estás seguro de que quieres cerrar sesión?')) {
            event.preventDefault();
            return;
        }

        localStorage.removeItem('authToken');
        sessionStorage.removeItem('authToken');
    });
});
